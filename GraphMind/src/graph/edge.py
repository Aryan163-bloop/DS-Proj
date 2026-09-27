"""
Edge: a directed relationship between two nodes.

An Edge always has semantic direction (source -> target). Whether a
Graph *treats* that direction as meaningful (directed graph) or mirrors
it both ways (undirected graph) is a decision made by the Graph class,
not by Edge itself. This keeps Edge simple and reusable.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .exceptions import InvalidNodeIDError, InvalidWeightError


class Edge:
    """
    Represents a directed relationship from a source node to a target node.

    Attributes:
        source: node_id of the source node.
        target: node_id of the target node.
        relation: the relationship type/label (e.g. "knows", "part_of").
        weight: optional numeric weight, defaults to 1.0. Must be a finite,
            non-negative number.
        properties: optional dict of arbitrary metadata.

    Note:
        Edge does not check that `source`/`target` actually exist in any
        particular graph — that is the Graph's responsibility, since Edge
        has no reference to a graph instance.

    Complexity:
        Construction, attribute access, __eq__, and __hash__ are O(1).
        __eq__/__hash__ are based on (source, target, relation), which is
        what identifies a *distinct* logical edge (two different relations
        between the same pair of nodes are distinct edges).
    """

    __slots__ = ("_source", "_target", "_relation", "_weight", "_properties")

    def __init__(
        self,
        source: str,
        target: str,
        relation: str = "related_to",
        weight: float = 1.0,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        for name, value in (("source", source), ("target", target)):
            if not isinstance(value, str) or value.strip() == "":
                raise InvalidNodeIDError(
                    f"{name} must be a non-empty string, got {value!r}"
                )
        if not isinstance(relation, str) or relation.strip() == "":
            raise InvalidNodeIDError(
                f"relation must be a non-empty string, got {relation!r}"
            )
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise InvalidWeightError(
                f"weight must be a number, got {weight!r}"
            )
        if math.isnan(weight) or math.isinf(weight):
            raise InvalidWeightError(
                f"weight must be finite, got {weight!r}"
            )
        if weight < 0:
            raise InvalidWeightError(
                f"weight must be non-negative, got {weight!r}"
            )
        if properties is not None and not isinstance(properties, dict):
            raise InvalidNodeIDError(
                f"properties must be a dict or None, got {properties!r}"
            )

        self._source = source
        self._target = target
        self._relation = relation
        self._weight = float(weight)
        self._properties = dict(properties) if properties else {}

    @property
    def source(self) -> str:
        return self._source

    @property
    def target(self) -> str:
        return self._target

    @property
    def relation(self) -> str:
        return self._relation

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def properties(self) -> dict[str, Any]:
        return dict(self._properties)

    def get_property(self, key: str, default: Any = None) -> Any:
        return self._properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        self._properties[key] = value

    def is_self_loop(self) -> bool:
        return self._source == self._target

    def reversed(self) -> "Edge":
        """
        Return a new Edge with source/target swapped, same relation,
        weight, and properties. Used internally by Graph to mirror
        edges for undirected graphs. O(1) (properties dict is copied,
        so O(P) where P = number of properties).
        """
        return Edge(
            self._target,
            self._source,
            relation=self._relation,
            weight=self._weight,
            properties=self._properties,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return (
            self._source == other._source
            and self._target == other._target
            and self._relation == other._relation
        )

    def __hash__(self) -> int:
        return hash((self._source, self._target, self._relation))

    def __repr__(self) -> str:
        return (
            f"Edge(source={self._source!r}, target={self._target!r}, "
            f"relation={self._relation!r}, weight={self._weight!r}, "
            f"properties={self._properties!r})"
        )

    def __str__(self) -> str:
        return f"{self._source} -[{self._relation}, w={self._weight}]-> {self._target}"
