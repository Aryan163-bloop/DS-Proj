import pytest

from src.graph.edge import Edge
from src.graph.exceptions import (
    EdgeAlreadyExistsError,
    EdgeNotFoundError,
    InvalidNodeIDError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    SelfLoopNotAllowedError,
)
from src.graph.graph import Graph
from src.graph.node import Node


def make_node(node_id, **kwargs):
    return Node(node_id, **kwargs)


# ----------------------------------------------------------------------
# Empty graph
# ----------------------------------------------------------------------

def test_empty_graph():
    g = Graph()
    assert g.nodeCount() == 0
    assert g.edgeCount() == 0
    assert g.getNodes() == []
    assert g.getEdges() == []
    assert not g.hasNode("missing")
    assert not g.hasEdge("a", "b")
    assert len(g) == 0
    assert "a" not in g


# ----------------------------------------------------------------------
# Adding nodes
# ----------------------------------------------------------------------

def test_add_node():
    g = Graph()
    g.addNode(make_node("a", label="Alice"))
    assert g.nodeCount() == 1
    assert g.hasNode("a")
    assert g.getNode("a").label == "Alice"
    assert "a" in g


def test_add_multiple_nodes():
    g = Graph()
    for nid in ("a", "b", "c"):
        g.addNode(make_node(nid))
    assert g.nodeCount() == 3
    ids = {n.node_id for n in g.getNodes()}
    assert ids == {"a", "b", "c"}


def test_add_duplicate_node_raises():
    g = Graph()
    g.addNode(make_node("a"))
    with pytest.raises(NodeAlreadyExistsError):
        g.addNode(make_node("a"))
    assert g.nodeCount() == 1  # unaffected by failed attempt


def test_add_non_node_raises():
    g = Graph()
    with pytest.raises(InvalidNodeIDError):
        g.addNode("not a node")


# ----------------------------------------------------------------------
# Removing nodes
# ----------------------------------------------------------------------

def test_remove_node():
    g = Graph()
    g.addNode(make_node("a"))
    g.removeNode("a")
    assert g.nodeCount() == 0
    assert not g.hasNode("a")


def test_remove_nonexistent_node_raises():
    g = Graph()
    with pytest.raises(NodeNotFoundError):
        g.removeNode("ghost")


def test_remove_node_cleans_up_incident_edges_directed():
    g = Graph(directed=True)
    for nid in ("a", "b", "c"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    g.addEdge(Edge("b", "c"))
    g.addEdge(Edge("c", "a"))
    assert g.edgeCount() == 3

    g.removeNode("b")
    assert g.nodeCount() == 2
    # edge a->b and b->c should be gone; c->a should remain
    assert g.edgeCount() == 1
    assert g.hasEdge("c", "a")
    assert not g.hasEdge("a", "b")
    assert not g.hasEdge("b", "c")
    # Neither remaining node should still reference b
    assert "b" not in g.adjacency_snapshot()
    for neighbors in g.adjacency_snapshot().values():
        assert "b" not in neighbors


def test_remove_node_cleans_up_incident_edges_undirected():
    g = Graph(directed=False)
    for nid in ("a", "b", "c"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    g.addEdge(Edge("b", "c"))
    assert g.edgeCount() == 2

    g.removeNode("b")
    assert g.nodeCount() == 2
    assert g.edgeCount() == 0
    assert not g.hasEdge("a", "b")
    assert not g.hasEdge("c", "b")


def test_remove_node_with_self_loop():
    g = Graph(directed=True, allow_self_loops=True)
    g.addNode(make_node("a"))
    g.addEdge(Edge("a", "a"))
    assert g.edgeCount() == 1
    g.removeNode("a")
    assert g.nodeCount() == 0
    assert g.edgeCount() == 0


# ----------------------------------------------------------------------
# getNode / hasNode
# ----------------------------------------------------------------------

def test_get_nonexistent_node_raises():
    g = Graph()
    with pytest.raises(NodeNotFoundError):
        g.getNode("ghost")


# ----------------------------------------------------------------------
# Adding edges
# ----------------------------------------------------------------------

def test_add_edge_directed():
    g = Graph(directed=True)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows"))
    assert g.hasEdge("a", "b")
    assert not g.hasEdge("b", "a")  # directed: no implicit reverse
    assert g.edgeCount() == 1


def test_add_edge_undirected():
    g = Graph(directed=False)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="friends_with"))
    assert g.hasEdge("a", "b")
    assert g.hasEdge("b", "a")  # undirected: mirrored
    assert g.edgeCount() == 1  # counted as a single logical edge


def test_add_edge_to_nonexistent_node_raises():
    g = Graph()
    g.addNode(make_node("a"))
    with pytest.raises(NodeNotFoundError):
        g.addEdge(Edge("a", "ghost"))
    with pytest.raises(NodeNotFoundError):
        g.addEdge(Edge("ghost", "a"))


def test_add_non_edge_raises():
    g = Graph()
    g.addNode(make_node("a"))
    with pytest.raises(InvalidNodeIDError):
        g.addEdge("not an edge")


def test_add_duplicate_edge_raises_by_default():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows"))
    with pytest.raises(EdgeAlreadyExistsError):
        g.addEdge(Edge("a", "b", relation="knows"))
    assert g.edgeCount() == 1


def test_add_duplicate_edge_allowed_when_configured():
    g = Graph(allow_duplicate_edges=True)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows", weight=1.0))
    g.addEdge(Edge("a", "b", relation="knows", weight=5.0))  # overwrite/upsert
    assert g.edgeCount() == 1
    edges = g.getEdges("a")
    assert len(edges) == 1
    assert edges[0].weight == 5.0


def test_multiple_relations_between_same_pair_allowed():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows"))
    g.addEdge(Edge("a", "b", relation="coworker_of"))
    assert g.edgeCount() == 2
    assert g.hasEdge("a", "b", relation="knows")
    assert g.hasEdge("a", "b", relation="coworker_of")
    assert not g.hasEdge("a", "b", relation="enemy_of")


def test_self_loop_allowed_by_default():
    g = Graph()
    g.addNode(make_node("a"))
    g.addEdge(Edge("a", "a", relation="self_ref"))
    assert g.hasEdge("a", "a")
    assert g.edgeCount() == 1


def test_self_loop_disallowed_when_configured():
    g = Graph(allow_self_loops=False)
    g.addNode(make_node("a"))
    with pytest.raises(SelfLoopNotAllowedError):
        g.addEdge(Edge("a", "a"))
    assert g.edgeCount() == 0


def test_weighted_edge():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", weight=4.2))
    edges = g.getEdges("a")
    assert edges[0].weight == 4.2


# ----------------------------------------------------------------------
# Removing edges
# ----------------------------------------------------------------------

def test_remove_edge_directed():
    g = Graph(directed=True)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b"))
    g.removeEdge("a", "b")
    assert not g.hasEdge("a", "b")
    assert g.edgeCount() == 0


def test_remove_edge_undirected_removes_both_directions():
    g = Graph(directed=False)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b"))
    g.removeEdge("a", "b")
    assert not g.hasEdge("a", "b")
    assert not g.hasEdge("b", "a")
    assert g.edgeCount() == 0


def test_remove_specific_relation_only():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows"))
    g.addEdge(Edge("a", "b", relation="coworker_of"))
    g.removeEdge("a", "b", relation="knows")
    assert not g.hasEdge("a", "b", relation="knows")
    assert g.hasEdge("a", "b", relation="coworker_of")
    assert g.edgeCount() == 1


def test_remove_all_relations_when_unspecified():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows"))
    g.addEdge(Edge("a", "b", relation="coworker_of"))
    g.removeEdge("a", "b")
    assert not g.hasEdge("a", "b")
    assert g.edgeCount() == 0


def test_remove_nonexistent_edge_raises():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    with pytest.raises(EdgeNotFoundError):
        g.removeEdge("a", "b")


def test_remove_edge_nonexistent_relation_raises():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b", relation="knows"))
    with pytest.raises(EdgeNotFoundError):
        g.removeEdge("a", "b", relation="enemy_of")


def test_remove_edge_nonexistent_node_raises():
    g = Graph()
    g.addNode(make_node("a"))
    with pytest.raises(NodeNotFoundError):
        g.removeEdge("a", "ghost")


# ----------------------------------------------------------------------
# hasEdge
# ----------------------------------------------------------------------

def test_has_edge_missing_endpoints_returns_false_not_raise():
    g = Graph()
    assert g.hasEdge("ghost1", "ghost2") is False


# ----------------------------------------------------------------------
# getNeighbors
# ----------------------------------------------------------------------

def test_get_neighbors():
    g = Graph(directed=True)
    for nid in ("a", "b", "c"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    g.addEdge(Edge("a", "c"))
    neighbors = {n.node_id for n in g.getNeighbors("a")}
    assert neighbors == {"b", "c"}
    assert g.getNeighbors("b") == []  # no outgoing edges


def test_get_neighbors_nonexistent_node_raises():
    g = Graph()
    with pytest.raises(NodeNotFoundError):
        g.getNeighbors("ghost")


def test_get_neighbors_undirected():
    g = Graph(directed=False)
    for nid in ("a", "b"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    assert {n.node_id for n in g.getNeighbors("a")} == {"b"}
    assert {n.node_id for n in g.getNeighbors("b")} == {"a"}


# ----------------------------------------------------------------------
# getEdges
# ----------------------------------------------------------------------

def test_get_edges_all_directed():
    g = Graph(directed=True)
    for nid in ("a", "b", "c"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    g.addEdge(Edge("b", "c"))
    edges = g.getEdges()
    assert len(edges) == 2


def test_get_edges_all_undirected_not_double_counted():
    g = Graph(directed=False)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "b"))
    edges = g.getEdges()
    assert len(edges) == 1  # not 2, despite internal mirroring


def test_get_edges_for_node():
    g = Graph(directed=True)
    for nid in ("a", "b", "c"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    g.addEdge(Edge("a", "c"))
    edges = g.getEdges("a")
    assert len(edges) == 2
    targets = {e.target for e in edges}
    assert targets == {"b", "c"}


def test_get_edges_nonexistent_node_raises():
    g = Graph()
    with pytest.raises(NodeNotFoundError):
        g.getEdges("ghost")


# ----------------------------------------------------------------------
# Counts
# ----------------------------------------------------------------------

def test_node_and_edge_counts_track_mutations():
    g = Graph()
    assert g.nodeCount() == 0 and g.edgeCount() == 0
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    assert g.nodeCount() == 2
    g.addEdge(Edge("a", "b"))
    assert g.edgeCount() == 1
    g.removeEdge("a", "b")
    assert g.edgeCount() == 0
    g.removeNode("a")
    assert g.nodeCount() == 1


# ----------------------------------------------------------------------
# Directed vs undirected configuration
# ----------------------------------------------------------------------

def test_directed_is_default():
    g = Graph()
    assert g.directed is True


def test_repr_reports_kind_and_counts():
    g = Graph(directed=False)
    g.addNode(make_node("a"))
    assert "undirected" in repr(g)
    assert "nodes=1" in repr(g)


# ----------------------------------------------------------------------
# adjacency_snapshot (used by the example script)
# ----------------------------------------------------------------------

def test_adjacency_snapshot():
    g = Graph(directed=True)
    for nid in ("a", "b", "c", "d"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("a", "b"))
    g.addEdge(Edge("a", "c"))
    g.addEdge(Edge("b", "d"))
    snap = g.adjacency_snapshot()
    assert set(snap["a"]) == {"b", "c"}
    assert snap["b"] == ["d"]
    assert snap["c"] == []
    assert snap["d"] == []
