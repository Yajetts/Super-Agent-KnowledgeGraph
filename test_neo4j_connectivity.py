"""Test Neo4j connectivity and graph statistics."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from graph.graph_manager import GraphManager
from config.settings import get_settings

def main():
    print("Testing Neo4j connectivity...")
    settings = get_settings()
    print(f"Neo4j URI: {settings.neo4j_uri}")
    print(f"Neo4j Username: {settings.neo4j_username}")
    
    try:
        graph_manager = GraphManager()
        driver = graph_manager.connect()
        print("✓ Neo4j connection established successfully")
        
        # Get graph statistics
        stats = graph_manager.get_stats()
        print(f"\nGraph Statistics:")
        print(f"  Tasks: {stats['tasks']}")
        print(f"  Agents: {stats['agents']}")
        print(f"  Findings: {stats['findings']}")
        print(f"  Risks: {stats['risks']}")
        print(f"  Recommendations: {stats['recommendations']}")
        
        total_nodes = sum(stats.values())
        print(f"\nTotal Nodes: {total_nodes}")
        
        # Get relationship count
        query = "MATCH ()-[r]->() RETURN count(r) as relationship_count"
        result = graph_manager.run_read(query)
        relationship_count = result[0]['relationship_count'] if result else 0
        print(f"Total Relationships: {relationship_count}")
        
        # Verify conditions
        if total_nodes == 0:
            print("\n✗ ERROR: Graph has zero nodes")
            return False
        
        if relationship_count == 0:
            print("\n✗ ERROR: Graph has zero relationships")
            return False
        
        print("\n✓ Graph statistics are valid (nodes > 0, relationships > 0)")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to connect to Neo4j: {e}")
        return False
    finally:
        if 'graph_manager' in locals():
            graph_manager.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
