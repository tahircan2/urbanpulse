import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from urbanpulse.langgraph_pipeline.graph import compiled_graph

def generate_diagram():
    try:
        # Generate Mermaid string
        mermaid_string = compiled_graph.get_graph().draw_mermaid()
        print("Mermaid Diagram Generated Successfully:")
        print("---")
        print(mermaid_string)
        print("---")
        
        # Try to save to file if user can use it
        with open("graph_diagram.mmd", "w", encoding="utf-8") as f:
            f.write(mermaid_string)
            
    except Exception as e:
        print(f"Error generating diagram: {e}")

if __name__ == "__main__":
    generate_diagram()
