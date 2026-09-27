# GraphMind — Architecture Plan

## 1. Scope of this session

This session implements **only** the foundational graph data structures:
`Node`, `Edge`, and `Graph` (adjacency-list based), with validation, error
handling, and unit tests. No traversal algorithms (BFS/DFS/Dijkstra/A*),
no auxiliary data structures (trie/hash table/heap), no persistence,
API, frontend, or ML/NLP components are implemented here. Those are
explicitly deferred to future sessions.

## 2. Project layout

```
GraphMind/
├── docs/
│   └── architecture.md        # this file
├── src/
│   ├── __init__.py
│   └── graph/
│       ├── __init__.py
│       ├── node.py            # Node class
│       ├── edge.py            # Edge class
│       ├── graph.py           # Graph class (adjacency list)
│       └── exceptions.py      # custom exception types
├── tests/
│   ├── __init__.py
│   ├── test_node.py
│   ├── test_edge.py
│   └── test_graph.py
├── benchmarks/
│   └── bench_graph.py         # simple timing benchmarks (no algorithms)
├── examples/
│   └── basic_usage.py         # A→B, A→C, B→D example
├── README.md
└── requirements.txt
```

Each concern lives in its own module. `Node` and `Edge` are plain data
holders with validation; `Graph` composes them and owns the adjacency
structure. This keeps each file small, independently testable, and easy
to extend later (e.g. adding indexing structures or traversal algorithms
without touching `Node`/`Edge`).

## 3. Core data model

### Node
- `node_id: str` — unique, immutable identifier.
- `label: str` — human-readable name.
- `type: str` — category/kind (e.g. "Person", "Concept").
- `properties: dict` — optional metadata, arbitrary key/value pairs.

### Edge
- `source: str` — source node id.
- `target: str` — destination node id.
- `relation: str` — relationship type (e.g. "knows", "part_of").
- `weight: float` — optional, defaults to `1.0`.
- `properties: dict` — optional metadata.

Edges are modeled as directed by construction (`source → target`). An
undirected graph is achieved at the `Graph` level by mirroring edges in
both adjacency directions, not by changing the `Edge` semantics. This
keeps `Edge` simple and lets `Graph` decide interpretation.

### Graph
- Owns a node table (`dict[node_id -> Node]`) for O(1) average-case
  node lookup.
- Owns an adjacency list (`dict[node_id -> dict[node_id -> Edge]]` for
  directed edges, plus a mirrored reverse-adjacency for directed graphs
  to support future in-degree/predecessor queries without scanning all
  edges).
- Configurable at construction time: `Graph(directed=True|False)`.

## 4. Why adjacency list, not adjacency matrix

Knowledge graphs are **sparse**: the number of real-world relationships
between entities is typically closer to O(N) or O(N log N) than O(N²).
An adjacency matrix allocates O(N²) space regardless of how many edges
actually exist, which is wasteful and quickly becomes infeasible as the
number of nodes grows (e.g. 1,000,000 nodes → 10^12 matrix cells).

An adjacency list instead allocates space proportional to what is
actually used: O(N + E). For a knowledge graph where most entities are
connected to a handful of others (not to everyone), this is dramatically
more space-efficient.

Adjacency lists are also a better fit for the operations a knowledge
graph engine needs most:
- **"Who/what is X connected to?"** (`getNeighbors`) is the dominant
  query pattern for graph traversal and reasoning. With an adjacency
  list this is O(1) to reach the neighbor set and O(degree) to iterate
  it. With a matrix it is O(N) regardless of actual degree, since every
  row must be scanned.
- **Adding/removing nodes** is cheap in a list-based structure (just add
  or remove a dict entry) but requires resizing/reindexing an entire
  matrix.
- Knowledge graphs grow incrementally (nodes and edges are added over
  time), which favors a structure that doesn't require pre-allocating
  a fixed-size N×N table.

The one thing an adjacency matrix is better at — O(1) "is there an edge
between X and Y" without hashing — is not a meaningful advantage here,
because a dict-based adjacency list gives O(1) average-case edge lookup
anyway (`hasEdge`) via nested hash maps.

## 5. Directed vs. undirected

The `Graph` class takes a `directed: bool` flag at construction:
- **Directed (default)**: `addEdge(a, b)` creates only `a → b`.
- **Undirected**: `addEdge(a, b)` creates both `a → b` and `b → a`
  internally, but they are treated as a single logical edge for
  `edgeCount()` and `removeEdge()`.

This is implemented once in `Graph`, not duplicated across two classes,
to avoid code duplication and divergence.

## 6. Error handling philosophy

Invalid operations raise explicit, typed exceptions (see
`src/graph/exceptions.py`) rather than failing silently or returning
`None`/`False` for programmer errors. Specifically:
- Duplicate node ID on `addNode` → `NodeAlreadyExistsError`.
- `addEdge`/`removeEdge` referencing a missing node → `NodeNotFoundError`.
- `removeNode` on a missing node → `NodeNotFoundError`.
- `removeEdge` on a missing edge → `EdgeNotFoundError`.
- Duplicate edge (same source, target, relation) on `addEdge` →
  `EdgeAlreadyExistsError` (unless `allow_duplicate_edges=True` is set
  at graph construction, since multigraphs are a legitimate knowledge
  graph use case — e.g. two different relations between the same pair
  is allowed by default since `relation` is part of edge identity;
  only exact (source, target, relation) duplicates are rejected).
- Negative/non-numeric weight → `InvalidWeightError`.
- Empty/None/non-string IDs → `InvalidNodeIDError`.
- Self-loops (`source == target`) are **allowed by default** (many
  knowledge graphs have legitimate self-referential relations, e.g.
  "Company X acquired Company X's subsidiary") but this is a documented
  configurable behavior (`allow_self_loops=True` by default on `Graph`).

`hasNode`, `hasEdge`, `getNeighbors` on a non-existent node behave as
documented per-method (see docstrings) — mostly returning
`False`/`[]` rather than raising, since these are "query" methods where
a negative answer is a valid answer, not an error.

## 7. Complexity summary (see also docstrings in code)

Assuming Python `dict` average-case O(1) hashing:

| Operation      | Time (avg)                | Space        | Notes |
|----------------|---------------------------|--------------|-------|
| addNode        | O(1)                      | O(1)         | dict insert |
| removeNode     | O(deg(v))                 | —            | must remove all incident edges |
| getNode        | O(1)                      | —            | dict lookup |
| hasNode        | O(1)                      | —            | dict lookup |
| addEdge        | O(1)                      | O(1)         | dict insert into adjacency map |
| removeEdge     | O(1)                      | —            | dict delete |
| hasEdge        | O(1)                      | —            | nested dict lookup |
| getNeighbors   | O(deg(v))                 | O(deg(v))    | returns a list snapshot |
| getNodes       | O(N)                      | O(N)         | full copy/list of all nodes |
| getEdges       | O(E)                      | O(E)         | iterates all adjacency entries |
| nodeCount      | O(1)                      | —            | maintained counter / len(dict) |
| edgeCount      | O(1)                      | —            | maintained counter |

N = number of nodes, E = number of edges, deg(v) = degree of node v.

These are average-case bounds for Python's hash-map-backed `dict`;
worst case for any individual hash operation is O(N) under pathological
hash collisions, which is standard and not specific to this design.

## 8. Testability & extensibility

- `Node` and `Edge` are simple, immutable-by-convention value objects
  with `__eq__`/`__repr__`, making them trivial to unit test in
  isolation.
- `Graph` exposes only the operations listed in the requirements; no
  traversal logic is embedded in it, so BFS/DFS/Dijkstra can be added
  later as separate modules that consume `Graph`'s public interface
  (`getNeighbors`, `getNodes`, etc.) without modifying `Graph` itself.
- Custom exceptions are centralized in one module so future code can
  catch them without importing internals.

## 9. Traversal algorithms (Session 2)

`src/graph/traversal.py` adds `bfs(graph, start_id)` and
`dfs(graph, start_id)`. Per section 8 above, both are implemented as
standalone functions, not methods on `Graph`, and use only `Graph`'s
public API (`getNode`, `getNeighbors`). No changes were made to `Node`,
`Edge`, or `Graph` to support them.

### BFS (Breadth-First Search)

Visits nodes level by level from `start_id`, using a FIFO queue
(`collections.deque`) and a `visited: set[str]` to avoid revisiting a
node. Returns a `list[Node]` in visitation order.

- **Time complexity: O(V + E)**, where **V** is the number of nodes
  reachable from `start_id` and **E** is the number of edges among
  them. Each reachable node is enqueued and dequeued exactly once
  (O(V)); when a node is dequeued, its outgoing edges are examined once
  via `getNeighbors()` (O(deg(v)) each), and summed across all
  dequeued nodes this is O(E).
- **Space complexity: O(V)**: the `visited` set, the queue, and the
  result list each hold at most one entry per reachable node.
- **Assumption**: `Graph.getNeighbors(v)` runs in O(deg(v)), which
  holds for this adjacency-list implementation (see section 7); the
  O(V + E) bound would not hold against a slower neighbor lookup (e.g.
  an adjacency matrix's O(N) row scan).

### DFS (Depth-First Search)

Visits as far as possible along each branch before backtracking, using
an **explicit stack** (a Python `list` used as a stack) rather than
recursion. Returns a `list[Node]` in visitation order.

**Why an explicit stack instead of recursion:** GraphMind's stated
purpose is "large knowledge graphs." A recursive DFS would use one
Python stack frame per node on the current path, and Python's default
recursion limit (~1000 frames) makes a recursive implementation raise
`RecursionError` on a sufficiently long chain of relations (e.g. a long
`part_of` or `derived_from` chain) -- a realistic shape for a knowledge
graph, not just a pathological edge case. An explicit stack has no such
limit beyond available memory, so it was chosen for correctness at
scale, not merely as a style preference.

- **Time complexity: O(V + E)**, same reasoning as BFS: each reachable
  node is expanded (has its neighbors examined) exactly once, and every
  edge from an expanded node is examined exactly once. (A node's id may
  be *pushed* onto the stack more than once, once per incoming edge
  from an already-visited node's perspective, but it is only ever
  *expanded* once, because the `visited` check happens on pop, before
  expansion.)
- **Space complexity: O(V)** for the `visited` set and result list. The
  explicit stack can hold up to O(E) entries in the worst case (a node
  can be pushed once per edge pointing to it before it is first
  popped), but for the sparse graphs this project targets (section 4),
  E is close to O(V), so this is effectively O(V) in practice; the
  worst-case bound is O(V + E).
- **Cycle safety**: a node already in `visited` is skipped when popped
  rather than re-expanded, so a cycle (including a self-loop) cannot
  cause infinite looping or unbounded stack growth.

### Definitions

- **V**: the number of distinct nodes reachable from the traversal's
  starting node (not necessarily every node in the graph -- see
  "disconnected graphs" below).
- **E**: the number of edges whose source node is reachable from the
  starting node (i.e. edges actually examined during the traversal).

### Behavior notes

- **Disconnected graphs**: both `bfs()` and `dfs()` only visit the
  connected component reachable from `start_id`. Nodes in other
  components are not included in the result and do not affect V/E for
  that call. Visiting every component requires calling `bfs`/`dfs`
  once per not-yet-visited node -- that is a distinct, higher-level
  operation and is not implemented here.
- **Nonexistent starting node**: both functions call
  `graph.getNode(start_id)` first, which raises `NodeNotFoundError` --
  the same exception `Graph.getNeighbors()` already raises for a
  missing node, so traversal error behavior is consistent with the
  rest of the public API rather than introducing a new error type.
- **Traversal order determinism**: neighbors are visited in the order
  `Graph.getNeighbors()` returns them, which is Python dict insertion
  order (the order `addEdge()` calls were made). This makes results
  reproducible for a fixed sequence of graph construction calls, but
  it is an implementation detail of `Graph`, not part of its documented
  contract.
