import pytest

from src.graph.edge import Edge
from src.graph.exceptions import NodeNotFoundError
from src.graph.graph import Graph
from src.graph.node import Node
from src.graph.traversal import bfs, dfs


def make_node(node_id, **kwargs):
    return Node(node_id, **kwargs)


def ids(nodes):
    return [n.node_id for n in nodes]


# ----------------------------------------------------------------------
# Empty graph / nonexistent starting node
# ----------------------------------------------------------------------

def test_bfs_nonexistent_start_raises():
    g = Graph()
    with pytest.raises(NodeNotFoundError):
        bfs(g, "ghost")


def test_dfs_nonexistent_start_raises():
    g = Graph()
    with pytest.raises(NodeNotFoundError):
        dfs(g, "ghost")


def test_bfs_nonexistent_start_on_nonempty_graph_raises():
    g = Graph()
    g.addNode(make_node("a"))
    with pytest.raises(NodeNotFoundError):
        bfs(g, "ghost")


def test_dfs_nonexistent_start_on_nonempty_graph_raises():
    g = Graph()
    g.addNode(make_node("a"))
    with pytest.raises(NodeNotFoundError):
        dfs(g, "ghost")


# ----------------------------------------------------------------------
# Single node
# ----------------------------------------------------------------------

def test_bfs_single_node():
    g = Graph()
    g.addNode(make_node("a"))
    result = bfs(g, "a")
    assert ids(result) == ["a"]


def test_dfs_single_node():
    g = Graph()
    g.addNode(make_node("a"))
    result = dfs(g, "a")
    assert ids(result) == ["a"]


def test_bfs_single_node_no_edges_returns_just_start():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))  # unrelated node, not connected to "a"
    result = bfs(g, "a")
    assert ids(result) == ["a"]


def test_dfs_single_node_no_edges_returns_just_start():
    g = Graph()
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    result = dfs(g, "a")
    assert ids(result) == ["a"]


# ----------------------------------------------------------------------
# Simple linear graph: A -> B -> C -> D
# ----------------------------------------------------------------------

def _linear_graph():
    g = Graph(directed=True)
    for nid in ("A", "B", "C", "D"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("A", "B"))
    g.addEdge(Edge("B", "C"))
    g.addEdge(Edge("C", "D"))
    return g


def test_bfs_linear_graph():
    g = _linear_graph()
    assert ids(bfs(g, "A")) == ["A", "B", "C", "D"]


def test_dfs_linear_graph():
    g = _linear_graph()
    assert ids(dfs(g, "A")) == ["A", "B", "C", "D"]


# ----------------------------------------------------------------------
# Branching graph / multiple levels:
#   A -> B, A -> C, B -> D, B -> E, C -> F
# ----------------------------------------------------------------------

def _branching_graph():
    g = Graph(directed=True)
    for nid in ("A", "B", "C", "D", "E", "F"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("A", "B"))
    g.addEdge(Edge("A", "C"))
    g.addEdge(Edge("B", "D"))
    g.addEdge(Edge("B", "E"))
    g.addEdge(Edge("C", "F"))
    return g


def test_bfs_branching_graph_visits_level_by_level():
    g = _branching_graph()
    result = ids(bfs(g, "A"))
    # Level 0: A. Level 1: B, C (in insertion order). Level 2: D, E, F.
    assert result == ["A", "B", "C", "D", "E", "F"]
    assert set(result) == {"A", "B", "C", "D", "E", "F"}


def test_dfs_branching_graph_goes_deep_before_wide():
    g = _branching_graph()
    result = ids(dfs(g, "A"))
    # DFS should exhaust A's first branch (B -> D, E) before backtracking
    # to A's second branch (C -> F).
    assert result == ["A", "B", "D", "E", "C", "F"]
    assert set(result) == {"A", "B", "C", "D", "E", "F"}


def test_bfs_and_dfs_visit_same_set_of_nodes():
    g = _branching_graph()
    assert set(ids(bfs(g, "A"))) == set(ids(dfs(g, "A")))


# ----------------------------------------------------------------------
# Cyclic graph: A -> B -> C -> A
# ----------------------------------------------------------------------

def _cyclic_graph():
    g = Graph(directed=True)
    for nid in ("A", "B", "C"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("A", "B"))
    g.addEdge(Edge("B", "C"))
    g.addEdge(Edge("C", "A"))  # closes the cycle
    return g


def test_bfs_handles_cycle_without_infinite_loop():
    g = _cyclic_graph()
    result = ids(bfs(g, "A"))
    assert result == ["A", "B", "C"]  # each node visited exactly once


def test_dfs_handles_cycle_without_infinite_loop():
    g = _cyclic_graph()
    result = ids(dfs(g, "A"))
    assert result == ["A", "B", "C"]


def test_bfs_and_dfs_handle_self_loop():
    g = Graph(directed=True, allow_self_loops=True)
    g.addNode(make_node("a"))
    g.addNode(make_node("b"))
    g.addEdge(Edge("a", "a"))  # self-loop
    g.addEdge(Edge("a", "b"))
    assert ids(bfs(g, "a")) == ["a", "b"]
    assert ids(dfs(g, "a")) == ["a", "b"]


def test_bfs_and_dfs_handle_undirected_cycle():
    # Undirected triangle: every addEdge mirrors both directions, so
    # this also exercises the "don't revisit" logic against edges that
    # loop straight back to the node they came from.
    g = Graph(directed=False)
    for nid in ("A", "B", "C"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("A", "B"))
    g.addEdge(Edge("B", "C"))
    g.addEdge(Edge("C", "A"))
    assert set(ids(bfs(g, "A"))) == {"A", "B", "C"}
    assert set(ids(dfs(g, "A"))) == {"A", "B", "C"}
    assert len(bfs(g, "A")) == 3  # no duplicates despite the cycle
    assert len(dfs(g, "A")) == 3


# ----------------------------------------------------------------------
# Disconnected graph
# ----------------------------------------------------------------------

def _disconnected_graph():
    g = Graph(directed=True)
    for nid in ("A", "B", "C", "D", "E"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("A", "B"))  # component 1: A, B
    g.addEdge(Edge("C", "D"))  # component 2: C, D
    # E is isolated (component 3)
    return g


def test_bfs_disconnected_graph_only_reaches_own_component():
    g = _disconnected_graph()
    assert set(ids(bfs(g, "A"))) == {"A", "B"}
    assert set(ids(bfs(g, "C"))) == {"C", "D"}
    assert set(ids(bfs(g, "E"))) == {"E"}


def test_dfs_disconnected_graph_only_reaches_own_component():
    g = _disconnected_graph()
    assert set(ids(dfs(g, "A"))) == {"A", "B"}
    assert set(ids(dfs(g, "C"))) == {"C", "D"}
    assert set(ids(dfs(g, "E"))) == {"E"}


# ----------------------------------------------------------------------
# Starting from different nodes
# ----------------------------------------------------------------------

def test_bfs_from_different_start_nodes_gives_different_results():
    g = _branching_graph()
    assert ids(bfs(g, "B")) == ["B", "D", "E"]
    assert ids(bfs(g, "C")) == ["C", "F"]
    assert ids(bfs(g, "D")) == ["D"]  # leaf node, no outgoing edges


def test_dfs_from_different_start_nodes_gives_different_results():
    g = _branching_graph()
    assert ids(dfs(g, "B")) == ["B", "D", "E"]
    assert ids(dfs(g, "C")) == ["C", "F"]
    assert ids(dfs(g, "D")) == ["D"]


# ----------------------------------------------------------------------
# No node is visited twice (diamond-shaped graph: A -> B, A -> C, B -> D, C -> D)
# ----------------------------------------------------------------------

def _diamond_graph():
    g = Graph(directed=True)
    for nid in ("A", "B", "C", "D"):
        g.addNode(make_node(nid))
    g.addEdge(Edge("A", "B"))
    g.addEdge(Edge("A", "C"))
    g.addEdge(Edge("B", "D"))
    g.addEdge(Edge("C", "D"))  # D is reachable via two different paths
    return g


def test_bfs_does_not_revisit_nodes_reached_via_multiple_paths():
    g = _diamond_graph()
    result = ids(bfs(g, "A"))
    assert result.count("D") == 1
    assert len(result) == 4


def test_dfs_does_not_revisit_nodes_reached_via_multiple_paths():
    g = _diamond_graph()
    result = ids(dfs(g, "A"))
    assert result.count("D") == 1
    assert len(result) == 4


# ----------------------------------------------------------------------
# Return type / contents
# ----------------------------------------------------------------------

def test_bfs_returns_actual_node_objects():
    g = _linear_graph()
    result = bfs(g, "A")
    assert all(isinstance(n, Node) for n in result)
    assert result[0] is g.getNode("A")


def test_dfs_returns_actual_node_objects():
    g = _linear_graph()
    result = dfs(g, "A")
    assert all(isinstance(n, Node) for n in result)
    assert result[0] is g.getNode("A")
