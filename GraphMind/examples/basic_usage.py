"""
Minimal demonstration of GraphMind's core data structures.

Builds the graph:
    A -> B
    A -> C
    B -> D

and prints the resulting adjacency list, exercising most of the public
Graph API in the process.

Run with:
    python -m examples.basic_usage
(from the project root)
"""

from src.graph import Edge, Graph, Node


def main() -> None:
    g = Graph(directed=True)

    for node_id in ("A", "B", "C", "D"):
        g.addNode(Node(node_id, label=f"Node {node_id}", type="demo"))

    g.addEdge(Edge("A", "B", relation="related_to"))
    g.addEdge(Edge("A", "C", relation="related_to"))
    g.addEdge(Edge("B", "D", relation="related_to"))

    print(f"Graph: {g!r}")
    print(f"Node count: {g.nodeCount()}")
    print(f"Edge count: {g.edgeCount()}\n")

    print("Neighbors:")
    for node_id in ("A", "B", "C", "D"):
        neighbor_ids = [n.node_id for n in g.getNeighbors(node_id)]
        print(f"  {node_id} -> {neighbor_ids}")

    print("\nResulting adjacency list:")
    for node_id, neighbors in g.adjacency_snapshot().items():
        print(f"  {node_id}: {neighbors}")


if __name__ == "__main__":
    main()
