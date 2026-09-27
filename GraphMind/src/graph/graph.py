"""
Graph: adjacency-list based knowledge graph container.

Design summary (see docs/architecture.md for full rationale):
  - Nodes are stored in a dict keyed by node_id for O(1) average lookup.
  - Edges are stored as a nested adjacency structure:
        _adjacency[u][v][relation] = Edge
    keyed by (source, target, relation) so that multiple distinct
    relationships between the same pair of nodes are supported
    (a knowledge graph is naturally a multigraph, e.g. "A -[knows]-> B"
    and "A -[coworker_of]-> B" are both valid simultaneously).
  - A parallel reverse-adjacency structure (_reverse_adjacency) is kept
    for directed graphs so predecessor-style queries and node removal
    do not require scanning every node's adjacency (which would be
    O(N) instead of O(deg(v))).
  - For undirected graphs, addEdge inserts the edge in both directions
    internally but it is accounted for as a single logical edge.

No traversal algorithms (BFS/DFS/etc.) live here by design; this class
only exposes structural operations.
"""

from __future__ import annotations

from typing import Any, Iterator, Optional

from .edge import Edge
from .exceptions import (
    EdgeAlreadyExistsError,
    EdgeNotFoundError,
    InvalidNodeIDError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    SelfLoopNotAllowedError,
)
from .node import Node


class Graph:
    """
    A knowledge graph backed by an adjacency list.

    Args:
        directed: If True (default), edges are one-directional
            (source -> target only). If False, every addEdge also
            creates the mirrored target -> source edge, and the two
            are treated as a single logical edge for counting/removal.
        allow_self_loops: If True (default), an edge from a node to
            itself is permitted. If False, adding a self-loop raises
            SelfLoopNotAllowedError.
        allow_duplicate_edges: If False (default), adding an edge with
            the same (source, target, relation) as an existing edge
            raises EdgeAlreadyExistsError. If True, addEdge overwrites
            the existing edge instead (upsert semantics).
    """

    def __init__(
        self,
        directed: bool = True,
        allow_self_loops: bool = True,
        allow_duplicate_edges: bool = False,
    ) -> None:
        self._directed = directed
        self._allow_self_loops = allow_self_loops
        self._allow_duplicate_edges = allow_duplicate_edges

        self._nodes: dict[str, Node] = {}
        # adjacency[u][v][relation] = Edge  (outgoing edges of u)
        self._adjacency: dict[str, dict[str, dict[str, Edge]]] = {}
        # reverse_adjacency[v][u][relation] = Edge  (incoming edges of v)
        self._reverse_adjacency: dict[str, dict[str, dict[str, Edge]]] = {}
        self._edge_count = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def directed(self) -> bool:
        return self._directed

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def addNode(self, node: Node) -> None:
        """
        Add a node to the graph.

        Raises:
            InvalidNodeIDError: if `node` is not a Node instance.
            NodeAlreadyExistsError: if a node with the same id already exists.

        Complexity: O(1) average case (dict insert).
        """
        if not isinstance(node, Node):
            raise InvalidNodeIDError(f"expected a Node instance, got {node!r}")
        if node.node_id in self._nodes:
            raise NodeAlreadyExistsError(
                f"node with id {node.node_id!r} already exists"
            )
        self._nodes[node.node_id] = node
        self._adjacency[node.node_id] = {}
        self._reverse_adjacency[node.node_id] = {}

    def removeNode(self, node_id: str) -> None:
        """
        Remove a node and all edges incident to it (incoming and outgoing).

        Raises:
            NodeNotFoundError: if no node with `node_id` exists.

        Complexity: O(deg(v)) where deg(v) is the total number of edges
        touching this node (incoming + outgoing), since each incident
        edge must be unlinked from its other endpoint's adjacency map.
        """
        self._require_node(node_id)

        if self._directed:
            # Outgoing edges: node_id is the source. Each entry here was
            # counted exactly once at insertion time (directed graphs
            # never mirror), so decrementing per-entry is safe.
            for target_id, relations in list(self._adjacency[node_id].items()):
                self._edge_count -= len(relations)
                self._reverse_adjacency[target_id].pop(node_id, None)

            # Incoming edges: node_id is the target (and not the source,
            # i.e. not a self-loop -- those were already handled above
            # since a self-loop lives under adjacency[node_id][node_id]).
            for source_id, relations in list(self._reverse_adjacency[node_id].items()):
                if source_id == node_id:
                    continue
                self._edge_count -= len(relations)
                self._adjacency[source_id].pop(node_id, None)
        else:
            # Undirected: every logical edge incident to node_id appears
            # exactly once as an entry in adjacency[node_id] (mirroring
            # happens on insert, so this already reflects the full
            # neighbor set). Iterating reverse_adjacency[node_id] as well
            # would double count, since it mirrors the same neighbors.
            for neighbor_id, relations in list(self._adjacency[node_id].items()):
                self._edge_count -= len(relations)
                if neighbor_id != node_id:
                    self._adjacency[neighbor_id].pop(node_id, None)
                    self._reverse_adjacency[neighbor_id].pop(node_id, None)

        del self._adjacency[node_id]
        del self._reverse_adjacency[node_id]
        del self._nodes[node_id]

    def getNode(self, node_id: str) -> Node:
        """
        Retrieve a node by id.

        Raises:
            NodeNotFoundError: if no node with `node_id` exists.

        Complexity: O(1) average case.
        """
        self._require_node(node_id)
        return self._nodes[node_id]

    def hasNode(self, node_id: str) -> bool:
        """
        Return whether a node with this id exists. Does not raise for a
        missing node -- a negative answer is a valid, expected result for
        this query method (see docs/architecture.md, section 6).

        Complexity: O(1) average case.
        """
        return node_id in self._nodes

    def getNodes(self) -> list[Node]:
        """
        Return a list of all nodes in the graph.

        Complexity: O(N) time and space, N = number of nodes.
        """
        return list(self._nodes.values())

    def nodeCount(self) -> int:
        """Complexity: O(1) (len() on a dict is O(1) in CPython)."""
        return len(self._nodes)

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def addEdge(self, edge: Edge) -> None:
        """
        Add an edge to the graph.

        For an undirected graph, this also inserts the mirrored
        (target -> source) edge internally; the pair is treated as one
        logical edge for edgeCount()/removeEdge().

        Raises:
            InvalidNodeIDError: if `edge` is not an Edge instance.
            NodeNotFoundError: if source or target node does not exist.
            SelfLoopNotAllowedError: if source == target and self-loops
                are disallowed on this graph.
            EdgeAlreadyExistsError: if an edge with the same
                (source, target, relation) already exists and
                allow_duplicate_edges is False.

        Complexity: O(1) average case (a constant number of dict inserts
        regardless of directed/undirected).
        """
        if not isinstance(edge, Edge):
            raise InvalidNodeIDError(f"expected an Edge instance, got {edge!r}")

        self._require_node(edge.source)
        self._require_node(edge.target)

        if edge.is_self_loop() and not self._allow_self_loops:
            raise SelfLoopNotAllowedError(
                f"self-loops are not allowed on this graph "
                f"(node {edge.source!r})"
            )

        existing = self._adjacency[edge.source].get(edge.target, {})
        if edge.relation in existing and not self._allow_duplicate_edges:
            raise EdgeAlreadyExistsError(
                f"edge {edge.source!r} -[{edge.relation}]-> {edge.target!r} "
                f"already exists"
            )

        is_new = edge.relation not in existing
        self._insert_directed(edge)

        if not self._directed and edge.source != edge.target:
            mirrored = edge.reversed()
            self._insert_directed(mirrored)

        if is_new:
            self._edge_count += 1

    def _insert_directed(self, edge: Edge) -> None:
        """Internal helper: insert a single directed edge entry, both
        into forward and reverse adjacency. O(1) average case."""
        self._adjacency.setdefault(edge.source, {}).setdefault(edge.target, {})[
            edge.relation
        ] = edge
        self._reverse_adjacency.setdefault(edge.target, {}).setdefault(
            edge.source, {}
        )[edge.relation] = edge

    def removeEdge(self, source: str, target: str, relation: Optional[str] = None) -> None:
        """
        Remove an edge (or all edges between source and target if
        `relation` is None).

        For an undirected graph, also removes the mirrored edge.

        Raises:
            NodeNotFoundError: if source or target node does not exist.
            EdgeNotFoundError: if no matching edge exists.

        Complexity: O(1) average case if `relation` is given (removing a
        single dict entry). O(k) if `relation` is None, where k is the
        number of distinct relations between source and target (usually
        small and bounded, not dependent on graph size).
        """
        self._require_node(source)
        self._require_node(target)

        relations = self._adjacency.get(source, {}).get(target, {})
        if not relations:
            raise EdgeNotFoundError(
                f"no edge exists between {source!r} and {target!r}"
            )

        if relation is not None:
            if relation not in relations:
                raise EdgeNotFoundError(
                    f"no edge {source!r} -[{relation}]-> {target!r} exists"
                )
            to_remove = [relation]
        else:
            to_remove = list(relations.keys())

        for rel in to_remove:
            self._remove_directed(source, target, rel)
            if not self._directed and source != target:
                self._remove_directed(target, source, rel)
            self._edge_count -= 1

    def _remove_directed(self, source: str, target: str, relation: str) -> None:
        """Internal helper: remove one directed edge entry from both
        forward and reverse adjacency. O(1) average case."""
        fwd = self._adjacency.get(source, {})
        if target in fwd:
            fwd[target].pop(relation, None)
            if not fwd[target]:
                del fwd[target]

        rev = self._reverse_adjacency.get(target, {})
        if source in rev:
            rev[source].pop(relation, None)
            if not rev[source]:
                del rev[source]

    def hasEdge(self, source: str, target: str, relation: Optional[str] = None) -> bool:
        """
        Return whether an edge exists between source and target
        (optionally restricted to a specific relation). Does not raise
        if source/target don't exist -- returns False instead, since a
        missing endpoint trivially implies no edge exists.

        Complexity: O(1) average case.
        """
        relations = self._adjacency.get(source, {}).get(target, {})
        if relation is None:
            return bool(relations)
        return relation in relations

    def getNeighbors(self, node_id: str) -> list[Node]:
        """
        Return the list of distinct nodes reachable via one outgoing
        edge from `node_id` (for an undirected graph, this is simply
        all adjacent nodes, since edges are mirrored).

        Raises:
            NodeNotFoundError: if no node with `node_id` exists.

        Complexity: O(deg(v)) time and space, where deg(v) is the
        out-degree (number of distinct neighbor ids) of the node.
        """
        self._require_node(node_id)
        neighbor_ids = self._adjacency[node_id].keys()
        return [self._nodes[nid] for nid in neighbor_ids]

    def getEdges(self, node_id: Optional[str] = None) -> list[Edge]:
        """
        Return all edges in the graph, or (if `node_id` is given) all
        outgoing edges from that node.

        For an undirected graph, getEdges() with no argument returns
        each logical edge once (not both mirrored directions).

        Raises:
            NodeNotFoundError: if `node_id` is given but doesn't exist.

        Complexity:
            getEdges(): O(E) time and space for a directed graph, or
                O(E) for an undirected graph as well (mirrored copies
                are de-duplicated before returning).
            getEdges(node_id): O(deg(v)) time and space.
        """
        if node_id is not None:
            self._require_node(node_id)
            edges = []
            for relations in self._adjacency[node_id].values():
                edges.extend(relations.values())
            return edges

        if self._directed:
            edges = []
            for relations_by_target in self._adjacency.values():
                for relations in relations_by_target.values():
                    edges.extend(relations.values())
            return edges

        # Undirected: adjacency stores both mirrored directions, so
        # de-duplicate using Edge equality (source, target, relation)
        # combined with its reverse to avoid double counting.
        seen: set[tuple[str, str, str]] = set()
        edges = []
        for relations_by_target in self._adjacency.values():
            for relations in relations_by_target.values():
                for e in relations.values():
                    key = tuple(sorted((e.source, e.target))) + (e.relation,)
                    if key not in seen:
                        seen.add(key)
                        edges.append(e)
        return edges

    def edgeCount(self) -> int:
        """
        Return the number of logical edges in the graph (for an
        undirected graph, a mirrored pair counts as one).

        Complexity: O(1) (maintained counter, updated incrementally by
        addEdge/removeEdge/removeNode).
        """
        return self._edge_count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise NodeNotFoundError(f"no node with id {node_id!r} exists")

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self.nodeCount()

    def __contains__(self, node_id: str) -> bool:
        return self.hasNode(node_id)

    def __repr__(self) -> str:
        kind = "directed" if self._directed else "undirected"
        return (
            f"Graph({kind}, nodes={self.nodeCount()}, edges={self.edgeCount()})"
        )

    def adjacency_snapshot(self) -> dict[str, list[str]]:
        """
        Return a simple {node_id: [neighbor_id, ...]} view of the
        adjacency list, useful for printing/demonstration purposes.

        Complexity: O(N + E) time and space.
        """
        return {
            node_id: list(neighbors.keys())
            for node_id, neighbors in self._adjacency.items()
        }
