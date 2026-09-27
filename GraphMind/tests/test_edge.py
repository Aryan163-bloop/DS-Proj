import math

import pytest

from src.graph.exceptions import InvalidNodeIDError, InvalidWeightError
from src.graph.edge import Edge


def test_create_edge_minimal():
    e = Edge("a", "b")
    assert e.source == "a"
    assert e.target == "b"
    assert e.relation == "related_to"
    assert e.weight == 1.0
    assert e.properties == {}


def test_create_edge_full():
    e = Edge("a", "b", relation="knows", weight=2.5, properties={"since": 2020})
    assert e.relation == "knows"
    assert e.weight == 2.5
    assert e.properties == {"since": 2020}


@pytest.mark.parametrize("bad_id", ["", "   ", None, 123])
def test_invalid_source_or_target_raises(bad_id):
    with pytest.raises(InvalidNodeIDError):
        Edge(bad_id, "b")
    with pytest.raises(InvalidNodeIDError):
        Edge("a", bad_id)


def test_invalid_relation_raises():
    with pytest.raises(InvalidNodeIDError):
        Edge("a", "b", relation="")


@pytest.mark.parametrize("bad_weight", [-1, -0.001, "heavy", True, math.nan, math.inf])
def test_invalid_weight_raises(bad_weight):
    with pytest.raises(InvalidWeightError):
        Edge("a", "b", weight=bad_weight)


def test_zero_weight_is_allowed():
    e = Edge("a", "b", weight=0)
    assert e.weight == 0.0


def test_invalid_properties_raises():
    with pytest.raises(InvalidNodeIDError):
        Edge("a", "b", properties="nope")


def test_is_self_loop():
    assert Edge("a", "a").is_self_loop()
    assert not Edge("a", "b").is_self_loop()


def test_reversed():
    e = Edge("a", "b", relation="knows", weight=3.0, properties={"x": 1})
    r = e.reversed()
    assert r.source == "b"
    assert r.target == "a"
    assert r.relation == "knows"
    assert r.weight == 3.0
    assert r.properties == {"x": 1}


def test_equality_based_on_source_target_relation():
    a = Edge("a", "b", relation="knows", weight=1.0)
    b = Edge("a", "b", relation="knows", weight=99.0, properties={"z": 1})
    c = Edge("a", "b", relation="dislikes")
    d = Edge("b", "a", relation="knows")
    assert a == b  # weight/properties don't affect identity
    assert a != c  # different relation
    assert a != d  # different direction
    assert a != "not an edge"


def test_hash_consistent_with_equality():
    a = Edge("a", "b", relation="knows")
    b = Edge("a", "b", relation="knows", weight=5.0)
    assert hash(a) == hash(b)


def test_repr_and_str():
    e = Edge("a", "b", relation="knows", weight=2.0)
    assert "knows" in repr(e)
    assert "a" in str(e) and "b" in str(e)
