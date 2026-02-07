"""
Base agent class with common functionality.

Demonstrates:
- Abstract base class pattern
- Common agent behaviors
- Azure OpenAI integration
- Error handling and retries
- Token usage tracking
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import time
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from config import get_settings, AgentPrompts
from utils.logger import AgentLogger
from utils.rate_limiter import RateLimiter, RateLimitConfig
from state.schemas import AgentState, add_message


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Provides:
    - Azure OpenAI client setup
    - Common execution patterns
    - Error handling and retries
    - Token tracking
    - Logging infrastructure
    """
    
    def __init__(self, name: str):
        self.name = name
        self.settings = get_settings()
        self.logger = AgentLogger(name)
        
        # Initialize Azure OpenAI client
        self.llm = self._setup_llm()
        
        # Initialize rate limiter
        rate_config = RateLimitConfig(
            requests_per_minute=self.settings.requests_per_minute,
            tokens_per_minute=self.settings.tokens_per_minute,
            max_concurrent=5
        )
        self.rate_limiter = RateLimiter(rate_config)
        
        # Tracking
        self.total_tokens_used = 0
        self.total_requests = 0
        self.errors = []
    
    # def _setup_llm(self) -> AzureChatOpenAI:
    #     """
    #     Setup Azure OpenAI LangChain client.
        
    #     Returns:
    #         Configured AzureChatOpenAI instance
    #     """
    #     return AzureChatOpenAI(
    #         azure_endpoint=self.settings.azure_openai_endpoint,
    #         api_key=self.settings.azure_openai_api_key,
    #         api_version=self.settings.azure_openai_api_version,
    #         deployment_name=self.settings.azure_openai_deployment_name,
    #         temperature=self.settings.model_temperature,
    #         max_tokens=self.settings.model_max_tokens,
    #         top_p=self.settings.model_top_p
    #     )
    

    def _setup_llm(self) -> AzureChatOpenAI:
        """Setup Azure OpenAI LangChain client."""
        return AzureChatOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            deployment_name=self.settings.azure_openai_deployment_name,
            temperature=self.settings.llm_temperature, 
            max_tokens=self.settings.llm_max_tokens,    
            top_p=self.settings.llm_top_p         
        )

    @abstractmethod
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute agent logic.
        
        Each agent must implement this method.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with state updates
        """
        pass
    
    def invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        Invoke LLM with retry logic and error handling.
        
        Args:
            system_prompt: System prompt for the LLM
            user_message: User message/query
            max_retries: Maximum retry attempts
            **kwargs: Additional arguments for LLM
            
        Returns:
            LLM response text
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        for attempt in range(max_retries):
            try:
                # Acquire rate limit
                if not self.rate_limiter.acquire():
                    raise RuntimeError("Rate limit exceeded")
                
                start_time = time.time()
                
                # Invoke LLM
                response = self.llm.invoke(messages, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Track usage
                self.total_requests += 1
                if hasattr(response, 'response_metadata'):
                    token_usage = response.response_metadata.get('token_usage', {})
                    tokens = token_usage.get('total_tokens', 0)
                    self.total_tokens_used += tokens
                
                # Release rate limit
                self.rate_limiter.release()
                
                self.logger.info(
                    f"LLM invocation successful",
                    duration=duration_ms,
                    attempt=attempt + 1
                )
                
                return response.content
                
            except Exception as e:
                self.rate_limiter.release()
                self.logger.warning(
                    f"LLM invocation failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                
                if attempt == max_retries - 1:
                    self.errors.append({
                        'timestamp': time.time(),
                        'error': str(e),
                        'type': type(e).__name__
                    })
                    raise
                
                # Exponential backoff
                time.sleep(2 ** attempt)
        
        raise RuntimeError(f"Failed after {max_retries} attempts")
    
    def invoke_llm_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: List[Any],
        max_retries: int = 3
    ) -> Any:
        """
        Invoke LLM with tool/function calling.
        
        Args:
            system_prompt: System prompt
            user_message: User message
            tools: List of tools/functions
            max_retries: Maximum retry attempts
            
        Returns:
            LLM response with potential tool calls
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        llm_with_tools = self.llm.bind_tools(tools)
        
        for attempt in range(max_retries):
            try:
                if not self.rate_limiter.acquire():
                    raise RuntimeError("Rate limit exceeded")
                
                response = llm_with_tools.invoke(messages)
                
                self.total_requests += 1
                self.rate_limiter.release()
                
                return response
                
            except Exception as e:
                self.rate_limiter.release()
                self.logger.warning(f"Tool invocation failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt == max_retries - 1:
                    raise
                
                time.sleep(2 ** attempt)
        
        raise RuntimeError(f"Failed after {max_retries} attempts")
    
    def add_message_to_state(
        self,
        state: AgentState,
        recipient: str,
        content: str,
        message_type: str = "task"
    ) -> Dict:
        """
        Helper to add message to state.
        
        Args:
            state: Current state
            recipient: Recipient agent name
            content: Message content
            message_type: Type of message
            
        Returns:
            State update dict
        """
        return add_message(state, self.name, recipient, content, message_type)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get agent execution statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            'agent_name': self.name,
            'total_requests': self.total_requests,
            'total_tokens_used': self.total_tokens_used,
            'total_errors': len(self.errors),
            'rate_limiter_stats': self.rate_limiter.get_stats()
        }
    
    def log_execution_start(self, state: AgentState):
        """Log agent execution start."""
        self.logger.log_task_start(
            task=state['task'],
            task_id=f"iter_{state['iteration_count']}"
        )
    
    def log_execution_end(self, state: AgentState, duration_ms: float):
        """Log agent execution end."""
        self.logger.log_task_complete(
            task=state['task'],
            duration_ms=duration_ms,
            task_id=f"iter_{state['iteration_count']}"
        )