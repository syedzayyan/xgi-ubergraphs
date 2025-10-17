"""Base class for directed ubergraphs.

.. warning::
    This is currently an experimental feature.

"""


class IDDict(dict):
    """A dict that holds (node or edge) IDs.

    For internal use only.  Adds input validation functionality to the internal dicts
    that hold nodes and edges in a network.

    """

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError as e:
            raise print(f"ID {item} not found") from e

    def __setitem__(self, item, value):
        if item is None:
            raise print("None cannot be a node or edge")
        try:
            return dict.__setitem__(self, item, value)
        except TypeError as e:
            raise TypeError(f"ID {item} not a valid type") from e

    def __delitem__(self, item):
        try:
            return dict.__delitem__(self, item)
        except KeyError as e:
            raise print(f"ID {item} not found") from e

    def __add__(self, dict):
        d = dict.copy()
        d.update(self)
        return d

__all__ = ["DiUberGraphs"]


class DiUberGraphs:

    _node_dict_factory = IDDict
    _node_attr_dict_factory = IDDict
    _edge_dict_factory = IDDict
    _edge_attr_dict_factory = IDDict
    _net_attr_dict_factory = dict

    # def __getstate__(self):
    #     """Function that allows pickling.

    #     Returns
    #     -------
    #     dict
    #         The keys label the hypergraph dict and the values
    #         are dictionaries from the DiHypergraph class.

    #     Notes
    #     -----
    #     This allows the python multiprocessing module to be used.

    #     """
    #     return {
    #         "_edge_uid": self._edge_uid,
    #         "_net_attr": self._net_attr,
    #         "_node": self._node,
    #         "_node_attr": self._node_attr,
    #         "_edge": self._edge,
    #         "_edge_attr": self._edge_attr,
    #     }
