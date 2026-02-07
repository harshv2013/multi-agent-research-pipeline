"""
Multi-agent flow example with detailed tracking.

Demonstrates:
- Step-by-step workflow execution
- Message flow between agents
- State inspection at each step
- Agent statistics
- Workflow visualization
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.graph_builder import create_workflow
from state.schemas import create_initial_state
from workflows.checkpointer import create_thread_id
from utils.logger import setup_logger
from utils.visualizer import WorkflowVisualizer


def print_state_summary(state_values: dict, step: int):
    """Print summary of current state."""
    print(f"\n{'=' * 80}")
    print(f"STEP {step} - Agent: {state_values.get('current_agent', 'unknown').upper()}")
    print('=' * 80)
    
    print(f"Iteration: {state_values.get('iteration_count', 0)}")
    print(f"Status: {state_values.get('workflow_status', 'unknown')}")
    print(f"Next Agent: {state_values.get('next_agent', 'unknown')}")
    
    # Show progress indicators
    print("\nProgress:")
    print(f"  Research: {'✓' if state_values.get('research_findings') else '✗'}")
    print(f"  Content: {'✓' if state_values.get('content_draft') else '✗'}")
    print(f"  Review: {'✓' if state_values.get('review_feedback') else '✗'}")
    
    # Show latest message
    messages = state_values.get('messages', [])
    if messages:
        latest = messages[-1]
        print(f"\nLatest Message:")
        print(f"  {latest.sender} → {latest.recipient}")
        print(f"  {latest.content[:150]}...")


def print_agent_statistics(workflow_builder):
    """Print statistics for all agents."""
    print("\n" + "=" * 80)
    print("AGENT STATISTICS")
    print("=" * 80)
    
    agents = {
        'Supervisor': workflow_builder.supervisor,
        'Researcher': workflow_builder.researcher,
        'Content Creator': workflow_builder.content_creator,
        'Reviewer': workflow_builder.reviewer
    }
    
    for name, agent in agents.items():
        stats = agent.get_statistics()
        print(f"\n{name}:")
        print(f"  Requests: {stats['total_requests']}")
        print(f"  Tokens Used: {stats['total_tokens_used']}")
        print(f"  Errors: {stats['total_errors']}")


def run_multi_agent_example():
    """Run multi-agent workflow with detailed tracking."""
    
    # Setup logging
    logger = setup_logger(
        name="multi_agent_example",
        log_level="INFO",
        log_file="logs/multi_agent_example.log",
        enable_console=True
    )
    
    print("=" * 80)
    print("MULTI-AGENT WORKFLOW EXAMPLE")
    print("=" * 80)
    
    # Define task
    task = "Research the impact of artificial intelligence on job markets and create a comprehensive article"
    
    print(f"\nTask: {task}\n")
    
    # Create initial state
    initial_state = create_initial_state(
        task=task,
        context={
            'content_type': 'article',
            'audience': 'professionals',
            'target_length': 'medium'
        }
    )
    
    # Create workflow
    print("Building workflow...")
    from workflows.graph_builder import WorkflowBuilder
    builder = WorkflowBuilder()
    workflow = builder.build()
    
    # Create thread ID
    thread_id = create_thread_id(task)
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"Thread ID: {thread_id}\n")
    
    # Execute with step tracking
    print("Executing workflow with step-by-step tracking...\n")
    
    try:
        step = 0
        for event in workflow.stream(initial_state, config):
            step += 1
            agent_name = list(event.keys())[0]
            
            # Get current state
            current_state = workflow.get_state(config)
            state_values = current_state.values
            
            # Print state summary
            print_state_summary(state_values, step)
            
            # Check if finished
            if state_values.get('next_agent') == 'finish':
                break
        
        # Get final state
        final_state = workflow.get_state(config)
        state_values = final_state.values
        
        # Print final results
        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETE")
        print("=" * 80)
        
        # Print message flow
        print("\n" + "=" * 80)
        print("MESSAGE FLOW")
        print("=" * 80)
        for i, msg in enumerate(state_values.get('messages', []), 1):
            print(f"\n{i}. [{msg.message_type.upper()}] {msg.sender} → {msg.recipient}")
            print(f"   Time: {msg.timestamp.strftime('%H:%M:%S')}")
            print(f"   Content: {msg.content[:200]}...")
        
        # Print agent statistics
        print_agent_statistics(builder)
        
        # Final output
        print("\n" + "=" * 80)
        print("FINAL OUTPUT")
        print("=" * 80)
        
        if state_values.get('final_output'):
            print(f"\n{state_values['final_output']}\n")
            
            metadata = state_values.get('metadata', {})
            print("\n" + "-" * 80)
            print("METADATA")
            print("-" * 80)
            print(f"Word Count: {metadata.get('word_count', 'N/A')}")
            print(f"Quality Score: {metadata.get('quality_score', 0):.2f}")
            print(f"Sources Used: {metadata.get('sources_used', 'N/A')}")
            print(f"Total Revisions: {metadata.get('revisions', 'N/A')}")
            print(f"Total Iterations: {state_values.get('iteration_count', 'N/A')}")
        else:
            print("\nWorkflow did not produce final output.")
            if state_values.get('errors'):
                print("\nErrors:")
                for error in state_values['errors']:
                    print(f"  - {error}")
        
        # Generate workflow visualization
        print("\n" + "=" * 80)
        print("GENERATING WORKFLOW DIAGRAM")
        print("=" * 80)
        
        visualizer = WorkflowVisualizer()
        dot_source = visualizer.create_workflow_diagram()
        
        # Save diagram
        output_dir = Path(__file__).parent.parent / "outputs"
        output_dir.mkdir(exist_ok=True)
        
        diagram_path = output_dir / "workflow_diagram"
        visualizer.save_diagram(str(diagram_path))
        
        print(f"\nWorkflow diagram saved to: {diagram_path}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"\nError: {e}")


if __name__ == "__main__":
    run_multi_agent_example()