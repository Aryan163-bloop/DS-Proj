"""
Basic timing comparison between BFS and DFS on generated graphs.

What this benchmark measures:
    Wall-clock time for a single full traversal (bfs() or dfs()) from a
    fixed start node, on randomly generated directed graphs of a few
    sizes. It measures THIS implementation's constant-factor overhead
    (Python function calls, deque vs list operations, set membership
    checks) on top of the shared O(V + E) asymptotic complexity that
    both algorithms have -- it does NOT show one algorithm being
    "faster" in an algorithmic sense, since BFS and DFS do the same
    asymptotic amount of work (each reachable node and edge is
    examined exactly once by both). Any timing difference here reflects
    implementation details (deque.popleft() vs list.pop(), the order
    memory is accessed in, etc.), not a complexity advantage of one
    algorithm over the other.

Run with:
    python -m benchmarks.bench_traversal
(from the project root)
"""

import random
import time

from src.graph import Edge, Graph, Node, bfs, dfs


def build_random_connected_graph(num_nodes: int, avg_out_degree: int, seed: int = 0) -> Graph:
    """
    Build a directed graph where node n{i} always has an edge to
    n{i+1} (guaranteeing every node is reachable from n0), plus extra
    random edges to reach roughly `avg_out_degree` on average.
    """
    rng = random.Random(seed)
    g = Graph(directed=True)
    for i in range(num_nodes):
        g.addNode(Node(f"n{i}"))

    for i in range(num_nodes - 1):
        g.addEdge(Edge(f"n{i}", f"n{i + 1}"))  # guarantees full reachability from n0

    extra_edges_per_node = max(0, avg_out_degree - 1)
    for i in range(num_nodes):
        for _ in range(extra_edges_per_node):
            j = rng.randrange(num_nodes)
            if j != i and not g.hasEdge(f"n{i}", f"n{j}"):
                g.addEdge(Edge(f"n{i}", f"n{j}"))

    return g


def time_it(label: str, fn) -> float:
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"  {label}: {elapsed * 1000:.3f} ms")
    return elapsed


def run_benchmark(num_nodes: int, avg_out_degree: int) -> None:
    g = build_random_connected_graph(num_nodes, avg_out_degree)
    print(f"\n--- num_nodes={num_nodes}, avg_out_degree={avg_out_degree}, "
          f"actual edgeCount()={g.edgeCount()} ---")

    time_it("bfs(g, 'n0')", lambda: bfs(g, "n0"))
    time_it("dfs(g, 'n0')", lambda: dfs(g, "n0"))

    # Sanity check: both should reach every node, since the graph was
    # built to be fully connected from n0.
    bfs_visited = len(bfs(g, "n0"))
    dfs_visited = len(dfs(g, "n0"))
    print(f"  nodes visited -- bfs: {bfs_visited}, dfs: {dfs_visited} "
          f"(graph has {g.nodeCount()} nodes)")


if __name__ == "__main__":
    for n in (1_000, 10_000, 50_000):
        run_benchmark(n, avg_out_degree=4)
