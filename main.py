"""
Main entry point for multi-agent research pipeline.

Usage:
    python main.py "Your research task here"
    python main.py "Research AI ethics" --content-type article --verbose
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from workflows.graph_builder import create_workflow
from state.schemas import create_initial_state
from workflows.checkpointer import create_thread_id, get_checkpointer
from utils.logger import setup_logger
from config import get_settings


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research and Content Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Research the benefits of meditation"
  python main.py "Analyze quantum computing trends" --content-type report
  python main.py "Study climate change impacts" --verbose --save-output results.txt
        """
    )
    
    parser.add_argument(
        "task",
        type=str,
        help="Research task or topic to process"
    )
    
    parser.add_argument(
        "--content-type",
        type=str,
        default="blog post",
        choices=["blog post", "article", "report", "summary"],
        help="Type of content to generate (default: blog post)"
    )
    
    parser.add_argument(
        "--audience",
        type=str,
        default="general audience",
        help="Target audience (default: general audience)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--save-output",
        type=str,
        metavar="FILE",
        help="Save final output to file"
    )
    
    parser.add_argument(
        "--no-checkpointing",
        action="store_true",
        help="Disable state checkpointing"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Override max iterations (default from config)"
    )
    
    return parser.parse_args()


def save_output(content: str, filepath: str):
    """Save output to file."""
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nOutput saved to: {output_path}")


def main():
    """Main execution function."""
    
    # ============================================
    # HARDCODED VALUES FOR DEBUGGING
    # Change the task below to debug different queries
    # ============================================
    class DebugArgs:
        task = "Explain how transformer architecture works in deep learning"
        content_type = "article"
        audience = "software engineers"
        verbose = True
        save_output = None
        no_checkpointing = False
        max_iterations = None
    
    args = DebugArgs()
    # ============================================
    
    # Uncomment below to use command-line arguments instead
    # args = parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger(
        name="main",
        log_level=log_level,
        log_file="logs/main.log",
        enable_console=True
    )
    
    # Print header
    print("\n" + "=" * 80)
    print("MULTI-AGENT RESEARCH & CONTENT PIPELINE")
    print("=" * 80)
    print(f"\nTask: {args.task}")
    print(f"Content Type: {args.content_type}")
    print(f"Audience: {args.audience}")
    
    # Get settings
    settings = get_settings()
    
    # Override max iterations if specified
    if args.max_iterations:
        settings.max_iterations = args.max_iterations
        print(f"Max Iterations: {args.max_iterations}")
    
    print("\n" + "-" * 80 + "\n")
    
    try:
        # Create initial state
        initial_state = create_initial_state(
            task=args.task,
            context={
                'content_type': args.content_type,
                'audience': args.audience
            }
        )
        
        # Create workflow
        logger.info("Building workflow graph...")
        workflow = create_workflow(with_checkpointing=not args.no_checkpointing)
        
        # Create thread ID
        thread_id = create_thread_id(args.task)
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"Thread ID: {thread_id}")
        logger.info("Starting workflow execution...")
        
        # Execute workflow
        print("Executing workflow...\n")
        
        step = 0
        for event in workflow.stream(initial_state, config):
            step += 1
            agent_name = list(event.keys())[0]
            print(f"  Step {step}: {agent_name.upper()} completed")
            
            # Get current state for detailed logging
            if args.verbose:
                current_state = workflow.get_state(config)
                state_values = current_state.values
                
                print(f"    → Current Agent: {state_values.get('current_agent')}")
                print(f"    → Next Agent: {state_values.get('next_agent')}")
                print(f"    → Iteration: {state_values.get('iteration_count')}")
                print(f"    → Revision Count: {state_values.get('revision_count')}")
                print(f"    → Review Decision: {state_values.get('review_decision', 'N/A')}")
                print(f"    → Review Score: {state_values.get('review_score', 0):.2f}")
                
                # Show progress
                has_research = "✓" if state_values.get('research_findings') else "✗"
                has_content = "✓" if state_values.get('content_draft') else "✗"
                has_review = "✓" if state_values.get('review_feedback') else "✗"
                print(f"    → Progress: Research {has_research} | Content {has_content} | Review {has_review}")
                print()
        
        # Get final state
        final_state = workflow.get_state(config)
        state_values = final_state.values
        
        # Add debug info if no final output
        if not state_values.get('final_output'):
            print("\n" + "=" * 80)
            print("DEBUG INFORMATION")
            print("=" * 80)
            print(f"Workflow Status: {state_values.get('workflow_status')}")
            print(f"Final Iteration: {state_values.get('iteration_count')}")
            print(f"Revision Count: {state_values.get('revision_count')}")
            print(f"Last Review Decision: {state_values.get('review_decision')}")
            print(f"Last Review Score: {state_values.get('review_score', 0):.2f}")
            print(f"\nHas Research: {'Yes' if state_values.get('research_findings') else 'No'}")
            print(f"Has Content: {'Yes' if state_values.get('content_draft') else 'No'}")
            print(f"Has Review: {'Yes' if state_values.get('review_feedback') else 'No'}")
            
            # Show last content if available
            if state_values.get('content_draft'):
                print("\n" + "-" * 80)
                print("LAST CONTENT DRAFT (Not Approved)")
                print("-" * 80)
                print(state_values['content_draft'][:500] + "...\n")
                
                print("\n" + "-" * 80)
                print("LAST REVIEW FEEDBACK")
                print("-" * 80)
                print(state_values.get('review_feedback', 'No feedback available')[:500] + "...\n")
        
        # Display results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        if state_values.get('final_output'):
            # Print output
            print("\n" + state_values['final_output'] + "\n")
            
            # Print metadata
            metadata = state_values.get('metadata', {})
            print("\n" + "-" * 80)
            print("STATISTICS")
            print("-" * 80)
            print(f"Word Count: {metadata.get('word_count', 'N/A')}")
            print(f"Quality Score: {metadata.get('quality_score', 0):.2f}/1.0")
            print(f"Sources Used: {metadata.get('sources_used', 'N/A')}")
            print(f"Revisions: {metadata.get('revisions', 'N/A')}")
            print(f"Total Iterations: {state_values.get('iteration_count', 'N/A')}")
            
            # Save output if requested
            if args.save_output:
                save_output(state_values['final_output'], args.save_output)
            
            print("\n✓ Workflow completed successfully!")
            
        else:
            print("\n✗ Workflow did not produce final output.")
            
            if state_values.get('errors'):
                print("\nErrors encountered:")
                for error in state_values['errors']:
                    print(f"  - {error}")
            
            sys.exit(1)
        
        print("\n" + "=" * 80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Workflow interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        
        if args.verbose:
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()