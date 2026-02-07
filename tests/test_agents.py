"""
Unit tests for agent functionality.
"""
import pytest
from state.schemas import create_initial_state, AgentState
from agents import SupervisorAgent, ResearcherAgent, ContentCreatorAgent, ReviewerAgent


class TestSupervisorAgent:
    """Test supervisor agent functionality."""
    
    def test_supervisor_initialization(self):
        """Test supervisor initializes correctly."""
        supervisor = SupervisorAgent()
        assert supervisor.name == "supervisor"
        assert supervisor.llm is not None
        assert supervisor.decision_history == []
    
    def test_supervisor_execute(self):
        """Test supervisor execution."""
        supervisor = SupervisorAgent()
        state = create_initial_state("Test task")
        
        result = supervisor.execute(state)
        
        assert 'next_agent' in result
        assert result['next_agent'] in ['researcher', 'content_creator', 'reviewer', 'finish']


class TestResearcherAgent:
    """Test researcher agent functionality."""
    
    def test_researcher_initialization(self):
        """Test researcher initializes correctly."""
        researcher = ResearcherAgent()
        assert researcher.name == "researcher"
        assert researcher.data_extractor is not None
    
    def test_researcher_execute(self):
        """Test researcher execution."""
        researcher = ResearcherAgent()
        state = create_initial_state("Research AI trends")
        
        result = researcher.execute(state)
        
        assert 'research_findings' in result
        assert 'research_sources' in result
        assert 'research_quality_score' in result


class TestContentCreatorAgent:
    """Test content creator agent functionality."""
    
    def test_content_creator_initialization(self):
        """Test content creator initializes correctly."""
        creator = ContentCreatorAgent()
        assert creator.name == "content_creator"
    
    def test_content_creator_execute(self):
        """Test content creator execution."""
        creator = ContentCreatorAgent()
        state = create_initial_state("Create article")
        state['research_findings'] = "Sample research findings"
        
        result = creator.execute(state)
        
        assert 'content_draft' in result
        assert 'content_version' in result


class TestReviewerAgent:
    """Test reviewer agent functionality."""
    
    def test_reviewer_initialization(self):
        """Test reviewer initializes correctly."""
        reviewer = ReviewerAgent()
        assert reviewer.name == "reviewer"
        assert reviewer.validator is not None
    
    def test_reviewer_execute(self):
        """Test reviewer execution."""
        reviewer = ReviewerAgent()
        state = create_initial_state("Review content")
        state['content_draft'] = "Sample content to review"
        state['research_findings'] = "Sample research"
        
        result = reviewer.execute(state)
        
        assert 'review_score' in result
        assert 'review_feedback' in result
        assert 'review_decision' in result
        assert result['review_decision'] in ['approve', 'request_revision', 'reject']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])