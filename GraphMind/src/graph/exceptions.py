"""
Custom exception types for GraphMind's core data structures.

Centralizing exceptions here means callers can catch specific,
well-named error types instead of relying on generic ValueError/KeyError,
and future modules (e.g. traversal algorithms) can import just this
module without pulling in the rest of the graph implementation.
"""


class GraphMindError(Exception):
    """Base class for all GraphMind graph-related errors."""


class InvalidNodeIDError(GraphMindError):
    """Raised when a node ID is missing, empty, or not a string."""


class NodeAlreadyExistsError(GraphMindError):
    """Raised when attempting to add a node whose ID already exists."""


class NodeNotFoundError(GraphMindError):
    """Raised when an operation references a node ID that doesn't exist."""


class EdgeAlreadyExistsError(GraphMindError):
    """Raised when attempting to add an edge that already exists."""


class EdgeNotFoundError(GraphMindError):
    """Raised when attempting to remove/access an edge that doesn't exist."""


class InvalidWeightError(GraphMindError):
    """Raised when an edge weight is not a valid, finite, non-negative number."""


class SelfLoopNotAllowedError(GraphMindError):
    """Raised when a self-loop edge is added on a graph that disallows them."""
