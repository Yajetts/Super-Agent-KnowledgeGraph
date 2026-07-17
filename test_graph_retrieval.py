"""Test graph retrieval with a benchmark query."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from graph.context_builder import build_graph_context
from graph.query_engine import GraphQueryEngine
from graph.graph_manager import GraphManager

def main():
    print("Testing graph retrieval with benchmark query...")
    
    # Use first benchmark query
    test_query = "List advantages and disadvantages of autonomous vehicles"
    print(f"Test query: {test_query}")
    
    try:
        graph_manager = GraphManager()
        query_engine = GraphQueryEngine(graph_manager)
        
        # Execute graph retrieval
        context = build_graph_context(test_query, query_engine=query_engine)
        
        print(f"\nRetrieval Results:")
        print(f"  Related Tasks: {len(context.related_tasks)}")
        print(f"  Related Findings: {len(context.related_findings)}")
        print(f"  Related Risks: {len(context.related_risks)}")
        print(f"  Related Recommendations: {len(context.related_recommendations)}")
        
        # Check if results are not empty
        total_items = (len(context.related_tasks) + 
                      len(context.related_findings) + 
                      len(context.related_risks) + 
                      len(context.related_recommendations))
        
        print(f"\nTotal Retrieved Items: {total_items}")
        
        if total_items == 0:
            print("\n✗ ERROR: Graph retrieval returned zero items")
            return False
        
        # Show sample data
        if context.related_tasks:
            print(f"\nSample Task: {context.related_tasks[0].get('query', 'N/A')}")
        if context.related_findings:
            print(f"Sample Finding: {context.related_findings[0].get('content', 'N/A')[:100]}...")
        if context.related_risks:
            print(f"Sample Risk: {context.related_risks[0].get('description', 'N/A')[:100]}...")
        if context.related_recommendations:
            print(f"Sample Recommendation: {context.related_recommendations[0].get('content', 'N/A')[:100]}...")
        
        print("\n✓ Graph retrieval returned actual data")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to execute graph retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'graph_manager' in locals():
            graph_manager.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
