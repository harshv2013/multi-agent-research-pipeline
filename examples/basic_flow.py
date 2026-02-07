"""
Basic workflow example - simple single execution.

Demonstrates:
- Creating initial state
- Running workflow once
- Extracting results
- Basic error handling
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.graph_builder import create_workflow
from state.schemas import create_initial_state
from workflows.checkpointer import create_thread_id
from utils.logger import setup_logger


def run_basic_example():
    """Run a basic single-execution workflow."""
    
    # Setup logging
    logger = setup_logger(
        name="basic_example",
        log_level="INFO",
        enable_console=True
    )
    
    logger.info("=" * 60)
    logger.info("BASIC WORKFLOW EXAMPLE")
    logger.info("=" * 60)
    
    # Define task
    task = "Research and create a blog post about the benefits of exercise for mental health"
    
    logger.info(f"\nTask: {task}\n")
    
    # Create initial state
    initial_state = create_initial_state(
        task=task,
        context={'content_type': 'blog post', 'audience': 'general public'}
    )
    
    # Create workflow
    logger.info("Building workflow...")
    workflow = create_workflow(with_checkpointing=True)
    
    # Create thread ID for this run
    thread_id = create_thread_id(task)
    config = {"configurable": {"thread_id": thread_id}}
    
    logger.info(f"Thread ID: {thread_id}\n")
    
    # Execute workflow
    logger.info("Executing workflow...\n")
    
    try:
        # Stream execution events
        for event in workflow.stream(initial_state, config):
            agent_name = list(event.keys())[0]
            logger.info(f"→ Agent '{agent_name}' completed")
        
        # Get final state
        final_state = workflow.get_state(config)
        state_values = final_state.values
        
        # Display results
        logger.info("\n" + "=" * 60)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 60)
        
        print("\n" + "=" * 80)
        print("FINAL OUTPUT")
        print("=" * 80)
        
        if state_values.get('final_output'):
            print(f"\n{state_values['final_output']}\n")
            
            print("\n" + "-" * 80)
            print("METADATA")
            print("-" * 80)
            metadata = state_values.get('metadata', {})
            print(f"Word Count: {metadata.get('word_count', 'N/A')}")
            print(f"Quality Score: {metadata.get('quality_score', 'N/A')}")
            print(f"Sources Used: {metadata.get('sources_used', 'N/A')}")
            print(f"Revisions: {metadata.get('revisions', 'N/A')}")
            print(f"Total Iterations: {state_values.get('iteration_count', 'N/A')}")
        else:
            print("\nNo final output generated.")
            
            if state_values.get('errors'):
                print("\nErrors encountered:")
                for error in state_values['errors']:
                    print(f"  - {error}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"\nError: {e}")


if __name__ == "__main__":
    run_basic_example()