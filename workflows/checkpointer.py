"""
Checkpointing utilities for workflow state persistence.

Demonstrates:
- In-memory checkpointing
- State recovery
- Checkpoint management
- Thread-based state isolation
"""
from typing import Optional, Dict, Any
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
import json
from pathlib import Path

from utils.logger import get_logger


class MemoryCheckpointer(MemorySaver):
    """
    Extended MemorySaver with additional utilities.
    
    Provides:
    - State persistence across workflow runs
    - Checkpoint listing and inspection
    - State export/import
    - Cleanup utilities
    """
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("checkpointer")
        self.checkpoint_metadata: Dict[str, Dict] = {}
    
    def save_checkpoint(
        self,
        thread_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict] = None
    ):
        """
        Save checkpoint with metadata.
        
        Args:
            thread_id: Thread identifier
            state: State to checkpoint
            metadata: Optional metadata
        """
        self.checkpoint_metadata[thread_id] = {
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'state_keys': list(state.keys())
        }
        
        self.logger.info(f"Checkpoint saved for thread: {thread_id}")
    
    def list_checkpoints(self) -> Dict[str, Dict]:
        """
        List all checkpoints with metadata.
        
        Returns:
            Dictionary of thread_id -> metadata
        """
        return self.checkpoint_metadata.copy()
    
    def export_checkpoint(
        self,
        thread_id: str,
        output_path: str
    ) -> bool:
        """
        Export checkpoint to JSON file.
        
        Args:
            thread_id: Thread to export
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            checkpoint_data = {
                'thread_id': thread_id,
                'timestamp': datetime.now().isoformat(),
                'metadata': self.checkpoint_metadata.get(thread_id, {})
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            self.logger.info(f"Checkpoint exported to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def clear_checkpoints(self, thread_id: Optional[str] = None):
        """
        Clear checkpoints.
        
        Args:
            thread_id: Specific thread to clear, or None for all
        """
        if thread_id:
            if thread_id in self.checkpoint_metadata:
                del self.checkpoint_metadata[thread_id]
                self.logger.info(f"Cleared checkpoint for thread: {thread_id}")
        else:
            self.checkpoint_metadata.clear()
            self.logger.info("Cleared all checkpoints")


# Global checkpointer instance
_checkpointer_instance: Optional[MemoryCheckpointer] = None


def get_checkpointer() -> MemoryCheckpointer:
    """
    Get or create global checkpointer instance.
    
    Returns:
        MemoryCheckpointer singleton
    """
    global _checkpointer_instance
    if _checkpointer_instance is None:
        _checkpointer_instance = MemoryCheckpointer()
    return _checkpointer_instance


def create_thread_id(task: str) -> str:
    """
    Create unique thread ID for a task.
    
    Args:
        task: Task description
        
    Returns:
        Thread ID
    """
    import hashlib
    from datetime import datetime
    
    timestamp = datetime.now().isoformat()
    content = f"{task}:{timestamp}"
    hash_id = hashlib.md5(content.encode()).hexdigest()[:8]
    
    return f"thread_{hash_id}"