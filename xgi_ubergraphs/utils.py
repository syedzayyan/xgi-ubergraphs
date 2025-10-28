"""General utilities."""

import random
from collections import defaultdict
from copy import deepcopy
from functools import cache
from itertools import chain, combinations, count

__all__ = [
    "IDDict",
    "update_uid_counter",
]


class IDDict(dict):
    """A dict that holds (node or edge) IDs.

    For internal use only.  Adds input validation functionality to the internal dicts
    that hold nodes and edges in a network.

    """

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError as e:
            raise IDNotFound(f"ID {item} not found") from e

    def __setitem__(self, item, value):
        if item is None:
            raise XGIError("None cannot be a node or edge")
        try:
            return dict.__setitem__(self, item, value)
        except TypeError as e:
            raise TypeError(f"ID {item} not a valid type") from e

    def __delitem__(self, item):
        try:
            return dict.__delitem__(self, item)
        except KeyError as e:
            raise IDNotFound(f"ID {item} not found") from e

    def __add__(self, dict):
        d = dict.copy()
        d.update(self)
        return d


def update_uid_counter(H, idx):
    """
    Helper function to make sure the uid counter is set correctly after
    adding an edge with a user-provided ID.

    If we don't set the start of self._edge_uid correctly, it will start at 0,
    which will overwrite any existing edges when calling add_edge().  First, we
    use the somewhat convoluted float(e).is_integer() instead of using
    isinstance(e, int) because there exist integer-like numeric types (such as
    np.int32) which fail the isinstance() check.

    Parameters
    ----------
    H : xgi.Hypergraph
        Hypergraph of which to update the uid counter
    idx : any hashable type
        User-provided ID.

    """
    uid = next(H._edge_uid)
    if (
        not isinstance(idx, str)
        and not isinstance(idx, tuple)
        and float(idx).is_integer()
        and uid <= idx
    ):
        # tuple comes from merging edges and doesn't have as as_integer() method.
        start = int(idx) + 1
        # we set the start at one plus the maximum edge ID that is an integer,
        # because count() only yields integer IDs.
    else:
        start = uid
    H._edge_uid = count(start=start)

