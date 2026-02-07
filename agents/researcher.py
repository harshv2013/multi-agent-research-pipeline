"""
Research Agent - gathers and validates information.

Responsibilities:
- Perform web searches
- Extract and analyze information
- Validate source credibility
- Synthesize findings into structured research
"""
from typing import Dict, Any, List
import time

from .base_agent import BaseAgent
from config import AgentPrompts
from state.schemas import AgentState, ResearchOutput
from tools.web_search import web_search_tool, get_search_tool
from tools.data_extraction import DataExtractor
from tools.validation import validate_sources


class ResearcherAgent(BaseAgent):
    """
    Research agent that gathers and validates information.
    
    Process:
    1. Analyze research query
    2. Perform web searches
    3. Extract key information
    4. Validate sources
    5. Synthesize findings
    """
    
    def __init__(self):
        super().__init__(name="researcher")
        self.data_extractor = DataExtractor()
        self.search_tool = get_search_tool()
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute research process.
        
        Args:
            state: Current workflow state
            
        Returns:
            State updates with research findings
        """
        start_time = time.time()
        self.log_execution_start(state)
        
        try:
            # Get research query from state or task
            query = state.get('research_query') or state['task']
            
            self.logger.info(f"Starting research for: {query}")
            
            # Step 1: Perform web search
            search_results = self._perform_search(query)
            
            # Step 2: Extract and analyze information
            findings = self._analyze_search_results(search_results, query)
            
            # Step 3: Synthesize research
            research_output = self._synthesize_research(query, findings, search_results)
            
            # Prepare state updates
            updates = {
                'current_agent': self.name,
                'research_query': query,
                'research_findings': research_output['findings'],
                'research_sources': research_output['sources'],
                'research_quality_score': research_output['quality_score']
            }
            
            # Add completion message
            message_update = self.add_message_to_state(
                state,
                recipient='supervisor',
                content=f"Research completed. Quality score: {research_output['quality_score']:.2f}",
                message_type="result"
            )
            updates.update(message_update)
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_execution_end(state, duration_ms)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Research failed: {str(e)}")
            return {
                'current_agent': self.name,
                'research_findings': f"Research failed: {str(e)}",
                'research_sources': [],
                'research_quality_score': 0.0,
                'errors': [f"Research error: {str(e)}"]
            }
    
    def _perform_search(self, query: str, num_results: int = 5) -> str:
        """
        Perform web search for the query.
        
        Args:
            query: Search query
            num_results: Number of results to retrieve
            
        Returns:
            Formatted search results
        """
        self.logger.info(f"Searching for: {query}")
        
        try:
            results = web_search_tool(query, num_results)
            self.logger.info(f"Search completed, {num_results} results found")
            return results
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return f"Search failed: {str(e)}"
    
    def _analyze_search_results(self, search_results: str, query: str) -> Dict[str, Any]:
        """
        Analyze search results and extract key information.
        
        Args:
            search_results: Raw search results
            query: Original query
            
        Returns:
            Analyzed findings
        """
        # Extract key points
        key_points = self.data_extractor.extract_key_points(search_results, max_points=10)
        
        # Extract statistics
        statistics = self.data_extractor.extract_statistics(search_results)
        
        # Extract quotes
        quotes = self.data_extractor.extract_quotes(search_results)
        
        # Extract entities
        entities = self.data_extractor.extract_entities(search_results)
        
        return {
            'key_points': key_points,
            'statistics': statistics,
            'quotes': quotes,
            'entities': entities,
            'raw_results': search_results
        }
    
    def _synthesize_research(
        self,
        query: str,
        findings: Dict[str, Any],
        search_results: str
    ) -> ResearchOutput:
        """
        Synthesize research findings using LLM.
        
        Args:
            query: Research query
            findings: Extracted findings
            search_results: Raw search results
            
        Returns:
            ResearchOutput with synthesized findings
        """
        # Build context from findings
        context = self._build_research_context(findings)
        
        # Create synthesis prompt
        system_prompt = AgentPrompts.RESEARCHER
        user_prompt = f"""
Research Query: {query}

Extracted Information:
{context}

Raw Search Results:
{search_results[:2000]}...

Please synthesize this information into a comprehensive research report.

Structure your response as:
1. Main Findings (key discoveries and insights)
2. Supporting Evidence (statistics, facts, quotes)
3. Source Assessment (quality and credibility)
4. Knowledge Gaps (what's missing or unclear)
5. Recommendations (for content creation)

Provide detailed, well-organized research findings:
"""
        
        try:
            # Get synthesis from LLM
            synthesis = self.invoke_llm(system_prompt, user_prompt)
            
            # Extract sources from search results
            sources = self._extract_sources(search_results)
            
            # Validate sources
            source_validation = validate_sources(sources)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                findings,
                source_validation,
                len(synthesis)
            )
            
            return ResearchOutput(
                findings=synthesis,
                sources=sources,
                quality_score=quality_score,
                knowledge_gaps=self._identify_knowledge_gaps(findings),
                recommendations=self._generate_recommendations(findings)
            )
            
        except Exception as e:
            self.logger.error(f"Synthesis failed: {str(e)}")
            return ResearchOutput(
                findings=f"Synthesis failed: {str(e)}",
                sources=[],
                quality_score=0.0,
                knowledge_gaps=[],
                recommendations=""
            )
    
    def _build_research_context(self, findings: Dict[str, Any]) -> str:
        """Build formatted context from findings."""
        parts = []
        
        # Key points
        if findings['key_points']:
            parts.append("Key Points:")
            for i, kp in enumerate(findings['key_points'][:5], 1):
                parts.append(f"{i}. [{kp.category}] {kp.text}")
        
        # Statistics
        if findings['statistics']:
            parts.append("\nStatistics:")
            for stat in findings['statistics'][:5]:
                parts.append(f"- {stat['value']}: {stat['context']}")
        
        # Quotes
        if findings['quotes']:
            parts.append("\nRelevant Quotes:")
            for quote in findings['quotes'][:3]:
                parts.append(f'- "{quote}"')
        
        return "\n".join(parts)
    
    def _extract_sources(self, search_results: str) -> List[str]:
        """Extract URLs from search results."""
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, search_results)
        return list(set(urls))[:10]  # Unique URLs, max 10
    
    def _calculate_quality_score(
        self,
        findings: Dict[str, Any],
        source_validation: Dict,
        synthesis_length: int
    ) -> float:
        """Calculate research quality score."""
        score = 0.0
        
        # Key points found
        if findings['key_points']:
            score += min(len(findings['key_points']) * 0.05, 0.3)
        
        # Statistics present
        if findings['statistics']:
            score += min(len(findings['statistics']) * 0.05, 0.2)
        
        # Source credibility
        score += source_validation.get('credibility_score', 0) * 0.3
        
        # Synthesis length (completeness)
        if synthesis_length > 500:
            score += 0.2
        
        return min(score, 1.0)
    
    def _identify_knowledge_gaps(self, findings: Dict[str, Any]) -> List[str]:
        """Identify what information is missing."""
        gaps = []
        
        if not findings['statistics']:
            gaps.append("No statistical data found")
        
        if not findings['quotes']:
            gaps.append("No expert quotes or citations")
        
        if len(findings['key_points']) < 5:
            gaps.append("Limited key insights extracted")
        
        return gaps
    
    def _generate_recommendations(self, findings: Dict[str, Any]) -> str:
        """Generate recommendations for content creation."""
        recs = []
        
        if findings['statistics']:
            recs.append("Include statistical evidence to support claims")
        
        if findings['quotes']:
            recs.append("Use expert quotes for credibility")
        
        if findings['key_points']:
            recs.append(f"Focus on {len(findings['key_points'])} main points identified")
        
        return "; ".join(recs) if recs else "Create comprehensive content based on findings"