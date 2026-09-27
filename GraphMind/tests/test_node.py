import pytest

from src.graph.exceptions import InvalidNodeIDError
from src.graph.node import Node


def test_create_node_minimal():
    n = Node("n1")
    assert n.node_id == "n1"
    assert n.label == "n1"  # defaults to node_id
    assert n.type == "default"
    assert n.properties == {}


def test_create_node_full():
    n = Node("n1", label="Alice", type="Person", properties={"age": 30})
    assert n.node_id == "n1"
    assert n.label == "Alice"
    assert n.type == "Person"
    assert n.properties == {"age": 30}


def test_properties_are_copied_not_referenced():
    props = {"age": 30}
    n = Node("n1", properties=props)
    props["age"] = 99
    assert n.properties == {"age": 30}  # unaffected by external mutation

    returned = n.properties
    returned["age"] = 12345
    assert n.get_property("age") == 30  # internal state untouched


def test_get_set_property():
    n = Node("n1")
    assert n.get_property("missing") is None
    assert n.get_property("missing", "default_val") == "default_val"
    n.set_property("color", "blue")
    assert n.get_property("color") == "blue"


@pytest.mark.parametrize("bad_id", ["", "   ", None, 123, 4.5])
def test_invalid_node_id_raises(bad_id):
    with pytest.raises(InvalidNodeIDError):
        Node(bad_id)


@pytest.mark.parametrize("bad_type", ["", "   ", 123])
def test_invalid_type_raises(bad_type):
    with pytest.raises(InvalidNodeIDError):
        Node("n1", type=bad_type)


def test_invalid_properties_raises():
    with pytest.raises(InvalidNodeIDError):
        Node("n1", properties="not_a_dict")


def test_equality_based_on_id_only():
    a = Node("n1", label="A", type="X")
    b = Node("n1", label="Different Label", type="Y")
    c = Node("n2", label="A", type="X")
    assert a == b  # same id -> equal, regardless of other fields
    assert a != c
    assert a != "n1"  # not equal to non-Node


def test_hash_consistent_with_equality():
    a = Node("n1")
    b = Node("n1", label="different")
    assert hash(a) == hash(b)
    s = {a, b}
    assert len(s) == 1


def test_repr_and_str():
    n = Node("n1", label="Alice", type="Person")
    assert "n1" in repr(n)
    assert "Alice" in str(n)
    assert "Person" in str(n)
