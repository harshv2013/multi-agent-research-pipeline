"""
Unit tests for workflow functionality.
"""
import pytest
from workflows.graph_builder import create_workflow, WorkflowBuilder
from workflows.checkpointer import get_checkpointer, create_thread_id
from state.schemas import create_initial_state


class TestWorkflowBuilder:
    """Test workflow builder functionality."""
    
    def test_workflow_builder_initialization(self):
        """Test workflow builder initializes correctly."""
        builder = WorkflowBuilder()
        assert builder.supervisor is not None
        assert builder.researcher is not None
        assert builder.content_creator is not None
        assert builder.reviewer is not None
    
    def test_workflow_build(self):
        """Test workflow builds without errors."""
        builder = WorkflowBuilder()
        workflow = builder.build()
        assert workflow is not None
    
    def test_workflow_with_checkpointing(self):
        """Test workflow builds with checkpointing."""
        checkpointer = get_checkpointer()
        builder = WorkflowBuilder()
        workflow = builder.build(checkpointer=checkpointer)
        assert workflow is not None


class TestWorkflowExecution:
    """Test workflow execution."""
    
    def test_simple_workflow_execution(self):
        """Test basic workflow execution."""
        workflow = create_workflow(with_checkpointing=True)
        initial_state = create_initial_state("Test task")
        
        thread_id = create_thread_id("test")
        config = {"configurable": {"thread_id": thread_id}}
        
        # Execute workflow (may take time with real API)
        # This is a smoke test
        try:
            events = list(workflow.stream(initial_state, config))
            assert len(events) > 0
        except Exception as e:
            # Expected if no API credentials configured
            assert "api" in str(e).lower() or "endpoint" in str(e).lower()


class TestCheckpointer:
    """Test checkpointing functionality."""
    
    def test_checkpointer_singleton(self):
        """Test checkpointer is singleton."""
        cp1 = get_checkpointer()
        cp2 = get_checkpointer()
        assert cp1 is cp2
    
    def test_thread_id_creation(self):
        """Test thread ID creation."""
        thread_id1 = create_thread_id("task1")
        thread_id2 = create_thread_id("task2")
        
        assert thread_id1.startswith("thread_")
        assert thread_id2.startswith("thread_")
        assert thread_id1 != thread_id2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])