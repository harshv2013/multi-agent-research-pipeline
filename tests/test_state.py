"""
Unit tests for state management.
"""
import pytest
from state.schemas import (
    AgentState,
    AgentMessage,
    create_initial_state,
    add_message,
    increment_iteration
)
from state.memory import MemoryManager, StateMemoryAdapter
from datetime import datetime


class TestAgentState:
    """Test agent state schemas."""
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state("Test task")
        
        assert state['task'] == "Test task"
        assert state['iteration_count'] == 0
        assert state['workflow_status'] == "running"
        assert state['current_agent'] == "supervisor"
        assert len(state['messages']) == 0
    
    def test_create_initial_state_with_context(self):
        """Test initial state with context."""
        context = {'content_type': 'article', 'custom': 'value'}
        state = create_initial_state("Test", context)
        
        assert state['user_context'] == context
        assert state['user_context']['content_type'] == 'article'


class TestAgentMessage:
    """Test agent message."""
    
    def test_agent_message_creation(self):
        """Test creating agent message."""
        msg = AgentMessage(
            sender="agent1",
            recipient="agent2",
            content="Test message",
            timestamp=datetime.now(),
            message_type="task"
        )
        
        assert msg.sender == "agent1"
        assert msg.recipient == "agent2"
        assert msg.message_type == "task"
    
    def test_agent_message_str(self):
        """Test message string representation."""
        msg = AgentMessage(
            sender="supervisor",
            recipient="researcher",
            content="Research this topic",
            timestamp=datetime.now(),
            message_type="task"
        )
        
        msg_str = str(msg)
        assert "supervisor" in msg_str
        assert "researcher" in msg_str


class TestStateHelpers:
    """Test state helper functions."""
    
    def test_add_message(self):
        """Test adding message to state."""
        state = create_initial_state("Test")
        
        update = add_message(state, "agent1", "agent2", "Hello")
        
        assert 'messages' in update
        assert len(update['messages']) == 1
        assert update['messages'][0].sender == "agent1"
    
    def test_increment_iteration(self):
        """Test incrementing iteration."""
        state = create_initial_state("Test")
        state['iteration_count'] = 5
        
        update = increment_iteration(state)
        
        assert update['iteration_count'] == 6


class TestMemoryManager:
    """Test memory management."""
    
    def test_memory_initialization(self):
        """Test memory manager initializes."""
        memory = MemoryManager(max_messages=10)
        assert memory.max_messages == 10
        assert len(memory.message_buffer) == 0
    
    def test_add_message_to_memory(self):
        """Test adding messages to memory."""
        memory = MemoryManager()
        
        msg = AgentMessage(
            sender="agent1",
            recipient="agent2",
            content="Test",
            timestamp=datetime.now(),
            message_type="task"
        )
        
        memory.add_message(msg)
        assert len(memory.message_buffer) == 1
    
    def test_get_recent_messages(self):
        """Test retrieving recent messages."""
        memory = MemoryManager()
        
        for i in range(5):
            msg = AgentMessage(
                sender=f"agent{i}",
                recipient="receiver",
                content=f"Message {i}",
                timestamp=datetime.now(),
                message_type="task"
            )
            memory.add_message(msg)
        
        recent = memory.get_recent_messages(n=3)
        assert len(recent) == 3
    
    def test_memory_statistics(self):
        """Test memory statistics."""
        memory = MemoryManager()
        
        msg = AgentMessage(
            sender="agent1",
            recipient="agent2",
            content="Test",
            timestamp=datetime.now(),
            message_type="task"
        )
        memory.add_message(msg)
        
        stats = memory.get_statistics()
        assert stats['current_messages'] == 1
        assert stats['total_processed'] == 1


class TestStateMemoryAdapter:
    """Test state memory adapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes."""
        memory = MemoryManager()
        adapter = StateMemoryAdapter(memory)
        assert adapter.memory is memory
    
    def test_sync_from_state(self):
        """Test syncing from state."""
        memory = MemoryManager()
        adapter = StateMemoryAdapter(memory)
        
        state = create_initial_state("Test")
        msg_update = add_message(state, "agent1", "agent2", "Hello")
        state['messages'] = msg_update['messages']
        
        adapter.sync_from_state(state)
        assert len(memory.message_buffer) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])