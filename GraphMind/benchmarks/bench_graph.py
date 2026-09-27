"""
Simple timing benchmarks for the core Graph structural operations
(addNode, addEdge, hasEdge, getNeighbors, removeNode).

This is NOT a benchmark of any traversal/search algorithm -- see
benchmarks/bench_traversal.py for BFS/DFS timing. It only measures the
cost of the structural operations implemented in src/graph/graph.py, to
sanity check that they behave close to their documented average-case
complexity as graph size grows.

Run with:
    python -m benchmarks.bench_graph
(from the project root)
"""

import random
import time

from src.graph import Edge, Graph, Node


def time_it(label: str, fn) -> None:
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    print(f"  {label}: {elapsed * 1000:.3f} ms")


def run_benchmark(num_nodes: int, avg_degree: int) -> None:
    print(f"\n--- num_nodes={num_nodes}, avg_degree={avg_degree} ---")

    g = Graph(directed=True)

    def add_nodes():
        for i in range(num_nodes):
            g.addNode(Node(f"n{i}"))

    time_it("addNode x N", add_nodes)

    rng = random.Random(42)
    edge_pairs = []
    for i in range(num_nodes):
        for _ in range(avg_degree):
            j = rng.randrange(num_nodes)
            if i != j:
                edge_pairs.append((i, j))

    def add_edges():
        for i, j in edge_pairs:
            if not g.hasEdge(f"n{i}", f"n{j}"):
                g.addEdge(Edge(f"n{i}", f"n{j}"))

    time_it(f"addEdge x ~{len(edge_pairs)}", add_edges)
    print(f"  actual edgeCount(): {g.edgeCount()}")

    sample_ids = [f"n{i}" for i in range(0, num_nodes, max(1, num_nodes // 100))]

    def lookup_neighbors():
        for nid in sample_ids:
            g.getNeighbors(nid)

    time_it(f"getNeighbors x {len(sample_ids)}", lookup_neighbors)

    def lookup_has_edge():
        for nid in sample_ids:
            g.hasEdge(nid, "n0")

    time_it(f"hasEdge x {len(sample_ids)}", lookup_has_edge)

    def remove_some_nodes():
        for nid in sample_ids:
            g.removeNode(nid)

    time_it(f"removeNode x {len(sample_ids)}", remove_some_nodes)


if __name__ == "__main__":
    for n in (1_000, 10_000, 50_000):
        run_benchmark(n, avg_degree=4)
