"""
Node: a vertex in the knowledge graph.

A Node is a lightweight, self-validating value object. It does not know
about the Graph it lives in — that separation keeps Node independently
testable and reusable.
"""

from __future__ import annotations

from typing import Any, Optional

from .exceptions import InvalidNodeIDError


class Node:
    """
    Represents a single entity (vertex) in the knowledge graph.

    Attributes:
        node_id: Unique identifier for this node. Must be a non-empty string.
        label: Human-readable name for the node (e.g. "Albert Einstein").
        type: Category/kind of the node (e.g. "Person", "Concept", "Event").
        properties: Optional dict of arbitrary metadata key/value pairs.

    Complexity:
        Construction, attribute access, __eq__, and __hash__ are all O(1)
        with respect to the graph size. __eq__/__hash__ are O(1) because
        they are based solely on node_id, not on properties.
    """

    __slots__ = ("_node_id", "_label", "_type", "_properties")

    def __init__(
        self,
        node_id: str,
        label: Optional[str] = None,
        type: str = "default",
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        if not isinstance(node_id, str) or node_id.strip() == "":
            raise InvalidNodeIDError(
                f"node_id must be a non-empty string, got {node_id!r}"
            )
        if not isinstance(type, str) or type.strip() == "":
            raise InvalidNodeIDError(
                f"type must be a non-empty string, got {type!r}"
            )
        if properties is not None and not isinstance(properties, dict):
            raise InvalidNodeIDError(
                f"properties must be a dict or None, got {properties!r}"
            )

        self._node_id = node_id
        self._label = label if label is not None else node_id
        self._type = type
        self._properties = dict(properties) if properties else {}

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def label(self) -> str:
        return self._label

    @property
    def type(self) -> str:
        return self._type

    @property
    def properties(self) -> dict[str, Any]:
        # Return a copy so external code cannot mutate internal state
        # without going through an explicit API.
        return dict(self._properties)

    def get_property(self, key: str, default: Any = None) -> Any:
        """O(1) average-case lookup of a single metadata property."""
        return self._properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        """O(1) average-case insert/update of a single metadata property."""
        self._properties[key] = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self._node_id == other._node_id

    def __hash__(self) -> int:
        return hash(self._node_id)

    def __repr__(self) -> str:
        return (
            f"Node(node_id={self._node_id!r}, label={self._label!r}, "
            f"type={self._type!r}, properties={self._properties!r})"
        )

    def __str__(self) -> str:
        return f"{self._label} ({self._type}) [id={self._node_id}]"
