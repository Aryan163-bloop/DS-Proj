"""
Demonstration of BFS and DFS traversal on a small directed graph.

Builds the graph:
    A -> B
    A -> C
    B -> D
    B -> E
    C -> F

and prints the BFS and DFS traversal orders starting from A.

Run with:
    python -m examples.traversal_demo
(from the project root)
"""

from src.graph import Edge, Graph, Node, bfs, dfs


def build_graph() -> Graph:
    g = Graph(directed=True)
    for node_id in ("A", "B", "C", "D", "E", "F"):
        g.addNode(Node(node_id, label=f"Node {node_id}", type="demo"))

    g.addEdge(Edge("A", "B"))
    g.addEdge(Edge("A", "C"))
    g.addEdge(Edge("B", "D"))
    g.addEdge(Edge("B", "E"))
    g.addEdge(Edge("C", "F"))
    return g


def main() -> None:
    g = build_graph()

    print(f"Graph: {g!r}")
    print("Adjacency list:")
    for node_id, neighbors in g.adjacency_snapshot().items():
        print(f"  {node_id}: {neighbors}")

    bfs_order = [n.node_id for n in bfs(g, "A")]
    dfs_order = [n.node_id for n in dfs(g, "A")]

    print(f"\nBFS traversal from A: {bfs_order}")
    print(f"DFS traversal from A: {dfs_order}")


if __name__ == "__main__":
    main()
