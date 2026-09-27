# GraphMind

GraphMind is a custom knowledge graph engine, built from scratch, whose
purpose is to efficiently store, modify, query, traverse, and analyze
large knowledge graphs — **without** relying on existing graph libraries
like NetworkX.

This is a **data structures and algorithms** project first and foremost.
It is not an AI/ML or NLP project.

## Current scope

**Session 1** implemented the foundational graph data structures:

- `Node` — a vertex with a unique id, label, type, and optional properties.
- `Edge` — a directed relationship between two nodes, with a relation
  type, optional weight, and optional properties.
- `Graph` — an adjacency-list based container supporting both directed
  and undirected configurations, full CRUD on nodes/edges, neighbor
  lookup, and counts.

**Session 2** added traversal algorithms on top of that, without
modifying `Node`, `Edge`, or `Graph`:

- `bfs(graph, start_id)` — Breadth-First Search, queue-based.
- `dfs(graph, start_id)` — Depth-First Search, iterative (explicit
  stack, not recursion -- see `docs/architecture.md` section 9 for why).

Explicitly **out of scope** so far: Dijkstra, A*, tries, hash tables
(beyond Python's built-in `dict`, which the adjacency list is built
on), heaps, a database layer, a REST API, a frontend, LLM/NLP
integration, embeddings, authentication, and containerization.

## Data structures

- **Adjacency list** (`dict[node_id -> dict[neighbor_id -> dict[relation -> Edge]]]`)
  rather than an adjacency matrix — see `docs/architecture.md` for the
  full rationale (short version: knowledge graphs are sparse, so an
  adjacency list uses O(N + E) space instead of O(N²), and its
  performance characteristics match the graph's actual query patterns).
- A parallel reverse-adjacency structure to support O(deg(v)) node
  removal instead of an O(N) scan.
- Node lookup is a flat `dict[node_id -> Node]` for O(1) average-case
  access.

See `docs/architecture.md` for the complete design rationale, the full
list of documented error conditions, and a per-operation complexity
table.

## Project structure

```
GraphMind/
├── docs/architecture.md      # design plan and complexity documentation
├── src/graph/                 # Node, Edge, Graph, traversal (bfs/dfs), exceptions
├── tests/                     # unit tests (pytest)
├── benchmarks/                # timing benchmarks for structural ops and traversal
├── examples/
│   ├── basic_usage.py          # Node/Edge/Graph worked example
│   └── traversal_demo.py       # BFS/DFS worked example
└── requirements.txt
```

## Running the tests

From the project root:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Running the example

```bash
python -m examples.basic_usage
python -m examples.traversal_demo
```

`basic_usage.py` builds the graph `A -> B`, `A -> C`, `B -> D` and
prints the resulting adjacency list. `traversal_demo.py` builds
`A -> B, A -> C, B -> D, B -> E, C -> F` and prints the BFS and DFS
traversal order from `A`.

## Running the benchmarks

```bash
python -m benchmarks.bench_graph
python -m benchmarks.bench_traversal
```

`bench_graph.py` times `addNode`, `addEdge`, `getNeighbors`, `hasEdge`,
and `removeNode` across a few graph sizes as a sanity check against the
documented average-case complexity. `bench_traversal.py` times `bfs()`
and `dfs()` on generated graphs of increasing size; see the docstring
at the top of that file for exactly what it does and does not show
(it does not claim one algorithm is asymptotically faster than the
other -- both are O(V + E)).

## Planned for future sessions

- Shortest-path algorithms: Dijkstra, A*.
- Additional supporting data structures as needed (e.g. a trie for
  label/prefix search, a heap for priority-based traversal).
- A persistence layer.
- A query/API layer.
- Higher-level graph analytics.
