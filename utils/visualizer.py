"""
Workflow visualization utilities.

Demonstrates:
- Graph visualization with Graphviz
- State flow diagrams
- Agent interaction maps
- Execution timeline
"""
from typing import Dict, List, Optional, Set
from pathlib import Path
import io


class WorkflowVisualizer:
    """
    Visualize LangGraph workflows and agent interactions.
    
    Creates diagrams showing:
    - Agent workflow graph
    - State transitions
    - Message flow between agents
    - Execution timeline
    """
    
    def __init__(self):
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []
        self.agent_colors = {
            'supervisor': '#4A90E2',
            'researcher': '#50C878',
            'content_creator': '#F5A623',
            'reviewer': '#E94B3C',
            'human': '#9B59B6'
        }
    
    def add_node(self, node_id: str, label: str, node_type: str = 'agent'):
        """Add node to visualization."""
        self.nodes.append({
            'id': node_id,
            'label': label,
            'type': node_type,
            'color': self.agent_colors.get(node_id, '#95A5A6')
        })
    
    def add_edge(
        self, 
        from_node: str, 
        to_node: str, 
        label: Optional[str] = None,
        edge_type: str = 'normal'
    ):
        """Add edge between nodes."""
        self.edges.append({
            'from': from_node,
            'to': to_node,
            'label': label or '',
            'type': edge_type
        })
    
    def generate_graphviz(self) -> str:
        """
        Generate Graphviz DOT notation.
        
        Returns:
            DOT format string
        """
        lines = [
            'digraph AgentWorkflow {',
            '    rankdir=TB;',
            '    node [shape=box, style=rounded, fontname="Arial"];',
            '    edge [fontname="Arial"];',
            ''
        ]
        
        # Add nodes
        for node in self.nodes:
            style = f'filled,rounded'
            lines.append(
                f'    {node["id"]} [label="{node["label"]}", '
                f'fillcolor="{node["color"]}", style="{style}"];'
            )
        
        lines.append('')
        
        # Add edges
        for edge in self.edges:
            label_part = f' [label="{edge["label"]}"]' if edge['label'] else ''
            style_part = ''
            
            if edge['type'] == 'conditional':
                style_part = ' [style=dashed]'
            elif edge['type'] == 'feedback':
                style_part = ' [color=red, style=dashed]'
            
            lines.append(
                f'    {edge["from"]} -> {edge["to"]}{label_part}{style_part};'
            )
        
        lines.append('}')
        
        return '\n'.join(lines)
    
    def save_diagram(self, output_path: str, format: str = 'png'):
        """
        Save diagram to file using Graphviz.
        
        Args:
            output_path: Output file path
            format: Output format (png, svg, pdf)
        """
        try:
            import graphviz
            
            dot_source = self.generate_graphviz()
            graph = graphviz.Source(dot_source)
            
            output_file = Path(output_path).with_suffix(f'.{format}')
            graph.render(output_file.stem, directory=output_file.parent, format=format, cleanup=True)
            
            print(f"Diagram saved to: {output_file}")
            
        except ImportError:
            print("Graphviz not installed. Saving DOT source only.")
            dot_file = Path(output_path).with_suffix('.dot')
            dot_file.write_text(self.generate_graphviz())
            print(f"DOT source saved to: {dot_file}")
        except Exception as e:
            print(f"Error generating diagram: {e}")
    
    def create_workflow_diagram(self) -> str:
        """
        Create standard multi-agent workflow diagram.
        
        Returns:
            Graphviz DOT notation
        """
        # Clear existing
        self.nodes.clear()
        self.edges.clear()
        
        # Add nodes
        self.add_node('start', 'START', 'start')
        self.add_node('supervisor', 'Supervisor\nAgent', 'agent')
        self.add_node('researcher', 'Research\nAgent', 'agent')
        self.add_node('content_creator', 'Content\nCreator', 'agent')
        self.add_node('reviewer', 'Review\nAgent', 'agent')
        self.add_node('human', 'Human\nReview', 'human')
        self.add_node('end', 'END', 'end')
        
        # Add edges
        self.add_edge('start', 'supervisor', 'User Task')
        self.add_edge('supervisor', 'researcher', 'Research Request')
        self.add_edge('researcher', 'supervisor', 'Research Results')
        self.add_edge('supervisor', 'content_creator', 'Create Content')
        self.add_edge('content_creator', 'supervisor', 'Draft Content')
        self.add_edge('supervisor', 'reviewer', 'Review Content')
        self.add_edge('reviewer', 'supervisor', 'Feedback')
        self.add_edge('supervisor', 'content_creator', 'Revision Request', 'feedback')
        self.add_edge('supervisor', 'human', 'Approval Needed', 'conditional')
        self.add_edge('human', 'supervisor', 'Approved/Rejected')
        self.add_edge('supervisor', 'end', 'Complete')
        
        return self.generate_graphviz()