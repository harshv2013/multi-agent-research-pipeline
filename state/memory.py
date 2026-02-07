"""
Memory management for agent state persistence and retrieval.

Demonstrates:
- Short-term memory (conversation context)
- Long-term memory (historical patterns)
- Memory summarization for context window management
"""
from typing import List, Dict, Optional
from datetime import datetime
from collections import deque
from .schemas import AgentMessage, AgentState


class MemoryManager:
    """
    Manages agent memory with sliding window and summarization.
    
    Features:
    - Sliding window for recent messages (short-term memory)
    - Summarization for older context (long-term memory)
    - Token-aware memory management
    - Retrieval by agent, time, or message type
    """
    
    def __init__(self, max_messages: int = 50, max_summary_length: int = 500):
        self.max_messages = max_messages
        self.max_summary_length = max_summary_length
        self.message_buffer: deque = deque(maxlen=max_messages)
        self.summarized_context: str = ""
        self.metadata: Dict = {
            "total_messages": 0,
            "last_summarization": None,
            "summarization_count": 0
        }
    
    def add_message(self, message: AgentMessage) -> None:
        """Add message to memory buffer."""
        self.message_buffer.append(message)
        self.metadata["total_messages"] += 1
        
        # Trigger summarization if buffer is full
        if len(self.message_buffer) >= self.max_messages:
            self._summarize_old_messages()
    
    def get_recent_messages(
        self, 
        n: int = 10, 
        agent: Optional[str] = None,
        message_type: Optional[str] = None
    ) -> List[AgentMessage]:
        """Retrieve recent messages with optional filtering."""
        messages = list(self.message_buffer)
        
        # Filter by agent
        if agent:
            messages = [
                m for m in messages 
                if m.sender == agent or m.recipient == agent
            ]
        
        # Filter by message type
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        # Return n most recent
        return messages[-n:]
    
    def get_conversation_history(self, max_tokens: int = 2000) -> str:
        """
        Get conversation history as string, respecting token limits.
        
        Combines summarized context with recent messages.
        Approximates tokens as chars/4 (rough estimate).
        """
        history_parts = []
        current_length = 0
        
        # Add summarized context first
        if self.summarized_context:
            summary_length = len(self.summarized_context)
            if summary_length < max_tokens * 4:
                history_parts.append(f"[Previous Context Summary]\n{self.summarized_context}\n")
                current_length += summary_length
        
        # Add recent messages
        recent_messages = list(self.message_buffer)
        recent_messages.reverse()  # Start from most recent
        
        for message in recent_messages:
            message_str = f"[{message.sender} → {message.recipient}]: {message.content}\n"
            message_length = len(message_str)
            
            if (current_length + message_length) < max_tokens * 4:
                history_parts.insert(1, message_str)  # Insert after summary
                current_length += message_length
            else:
                break
        
        return "\n".join(history_parts)
    
    def get_agent_interactions(self, agent_name: str) -> List[AgentMessage]:
        """Get all messages involving a specific agent."""
        return [
            m for m in self.message_buffer
            if m.sender == agent_name or m.recipient == agent_name
        ]
    
    def _summarize_old_messages(self) -> None:
        """
        Summarize older messages to save context space.
        This is a simple implementation; in production, use LLM for summarization.
        """
        if len(self.message_buffer) < 10:
            return
        
        # Take first half of messages for summarization
        messages_to_summarize = list(self.message_buffer)[:len(self.message_buffer) // 2]
        
        # Simple summarization: extract key transitions
        key_events = []
        for msg in messages_to_summarize:
            if msg.message_type in ["task", "result"]:
                key_events.append(f"{msg.sender} → {msg.recipient}: {msg.content[:100]}")
        
        # Update summarized context
        new_summary = "\n".join(key_events[:10])  # Keep top 10 events
        if self.summarized_context:
            self.summarized_context = f"{self.summarized_context}\n{new_summary}"
        else:
            self.summarized_context = new_summary
        
        # Trim summary if too long
        if len(self.summarized_context) > self.max_summary_length:
            self.summarized_context = self.summarized_context[-self.max_summary_length:]
        
        # Update metadata
        self.metadata["last_summarization"] = datetime.now()
        self.metadata["summarization_count"] += 1
    
    def clear(self) -> None:
        """Clear all memory."""
        self.message_buffer.clear()
        self.summarized_context = ""
        self.metadata = {
            "total_messages": 0,
            "last_summarization": None,
            "summarization_count": 0
        }
    
    def get_statistics(self) -> Dict:
        """Get memory usage statistics."""
        return {
            "current_messages": len(self.message_buffer),
            "max_messages": self.max_messages,
            "total_processed": self.metadata["total_messages"],
            "summarization_count": self.metadata["summarization_count"],
            "summary_length": len(self.summarized_context),
            "last_summarization": self.metadata["last_summarization"]
        }


class StateMemoryAdapter:
    """
    Adapter to integrate MemoryManager with AgentState.
    Bridges between LangGraph state and memory management.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    def sync_from_state(self, state: AgentState) -> None:
        """Sync messages from AgentState to MemoryManager."""
        for message in state["messages"]:
            self.memory.add_message(message)
    
    def get_context_for_agent(
        self, 
        agent_name: str, 
        state: AgentState,
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for a specific agent.
        Combines state information with memory.
        """
        # Sync latest messages
        self.sync_from_state(state)
        
        # Build context
        context_parts = [
            f"Current Task: {state['task']}",
            f"Workflow Status: {state['workflow_status']}",
            f"Current Agent: {state['current_agent']}",
            f"Iteration: {state['iteration_count']}/{10}",  # Assuming max 10
            "",
            "Recent Activity:",
            self.memory.get_conversation_history(max_tokens=max_tokens)
        ]
        
        return "\n".join(context_parts)
    
    def get_statistics(self) -> Dict:
        """Get memory statistics."""
        return self.memory.get_statistics()