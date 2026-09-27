"""
Graph traversal algorithms: Breadth-First Search (BFS) and
Depth-First Search (DFS).

These functions are intentionally kept OUTSIDE the Graph class (see
docs/architecture.md, section 8): they consume only Graph's public API
(`hasNode`, `getNode`, `getNeighbors`) and do not touch any private
adjacency structures. This keeps Graph free of algorithm-specific logic
and lets future algorithms (Dijkstra, A*, ...) be added the same way,
without modifying Graph itself.

Both functions:
  - Start from a given node id.
  - Return the traversal order as a list[Node].
  - Never revisit an already-visited node (safe on cyclic graphs).
  - Raise NodeNotFoundError for a nonexistent starting node, consistent
    with Graph.getNeighbors()/Graph.getNode()'s existing behavior.
  - Only visit nodes reachable from `start_id`. On a graph with
    disconnected components, nodes in other components are simply never
    reached -- callers who want "all nodes across all components" should
    call these functions once per unvisited node (not implemented here,
    since that is a different, higher-level operation than a single
    traversal).
  - Iterate a node's neighbors in the order Graph.getNeighbors() returns
    them, which is Python dict insertion order (the order edges were
    added). This makes traversal order deterministic and reproducible
    for a given sequence of addEdge() calls, but that order is an
    implementation detail of Graph, not a documented contract of Graph
    itself.
"""

from __future__ import annotations

from collections import deque

from .graph import Graph
from .node import Node


def bfs(graph: Graph, start_id: str) -> list[Node]:
    """
    Breadth-First Search from `start_id`.

    Visits nodes level by level (all nodes at distance 1 from start,
    then all nodes at distance 2, and so on), using a FIFO queue.

    Args:
        graph: the Graph to traverse.
        start_id: node_id to start from.

    Returns:
        A list of Node objects in BFS visitation order, starting with
        the start node itself.

    Raises:
        NodeNotFoundError: if `start_id` does not exist in `graph`
            (raised by graph.getNode(), consistent with how
            Graph.getNeighbors() already handles a missing node).

    Complexity:
        Time: O(V + E), where V is the number of nodes reachable from
            `start_id` and E is the number of edges among them. Each
            reachable node is enqueued/dequeued exactly once (O(V)),
            and each of its outgoing edges is examined exactly once
            when the node is dequeued (O(E) total across all nodes).
        Space: O(V) for the `visited` set, the queue, and the result
            list, each of which holds at most one entry per reachable
            node.

    Assumptions:
        - `graph.getNeighbors(v)` runs in O(deg(v)) (true for this
          Graph's adjacency-list implementation), which is what makes
          the O(V + E) bound hold; a slower getNeighbors would change
          this bound.
    """
    start_node = graph.getNode(start_id)  # raises NodeNotFoundError if missing

    visited: set[str] = {start_id}
    order: list[Node] = [start_node]
    queue: deque[str] = deque([start_id])

    while queue:
        current_id = queue.popleft()
        for neighbor in graph.getNeighbors(current_id):
            if neighbor.node_id not in visited:
                visited.add(neighbor.node_id)
                order.append(neighbor)
                queue.append(neighbor.node_id)

    return order


def dfs(graph: Graph, start_id: str) -> list[Node]:
    """
    Depth-First Search from `start_id`.

    Implementation choice: iterative, using an explicit stack, rather
    than recursion. This is a deliberate choice for a graph engine
    meant to handle "large knowledge graphs" (per the project's stated
    purpose): Python's default recursion limit (~1000 frames) means a
    recursive DFS would raise RecursionError on a sufficiently long
    path/chain, which is a realistic shape for a knowledge graph (e.g.
    a long chain of "part_of" or "derived_from" relations). An explicit
    stack has no such limit beyond available memory.

    Args:
        graph: the Graph to traverse.
        start_id: node_id to start from.

    Returns:
        A list of Node objects in DFS visitation order, starting with
        the start node itself.

    Raises:
        NodeNotFoundError: if `start_id` does not exist in `graph`.

    Complexity:
        Time: O(V + E), where V is the number of nodes reachable from
            `start_id` and E is the number of edges among them. Each
            reachable node is pushed/popped from the stack exactly once
            in the visited set's steady state (a node's id may be
            pushed more than once before it is first visited, but it is
            only ever expanded -- i.e. have its neighbors examined --
            once, and each edge is examined exactly once across the
            whole traversal).
        Space: O(V) for the `visited` set and the result list. The
            explicit stack holds at most O(E) entries in the worst case
            (a node can be pushed once per incoming edge before being
            visited), which is bounded by O(V + E) and, for the sparse
            graphs this project targets (see docs/architecture.md,
            section 4), is effectively O(V).

    Assumptions:
        - Same as bfs(): O(deg(v)) neighbor lookup via getNeighbors().
        - Cycles are handled safely: a node already in `visited` is
          skipped rather than re-expanded, so a cycle cannot cause
          infinite looping or unbounded stack growth.
    """
    start_node = graph.getNode(start_id)  # raises NodeNotFoundError if missing

    visited: set[str] = set()
    order: list[Node] = []
    stack: list[str] = [start_id]

    while stack:
        current_id = stack.pop()
        if current_id in visited:
            continue
        visited.add(current_id)
        order.append(graph.getNode(current_id))

        # Push neighbors in reverse so that, when popped (LIFO), they
        # are visited in the same left-to-right order getNeighbors()
        # returns them -- matching the intuitive/expected DFS order.
        neighbors = graph.getNeighbors(current_id)
        for neighbor in reversed(neighbors):
            if neighbor.node_id not in visited:
                stack.append(neighbor.node_id)

    return order
