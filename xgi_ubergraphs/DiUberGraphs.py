from xgi.utils import IDDict, update_uid_counter
from typing import Iterable
from itertools import count
import warnings
from xgi.core.views import DiEdgeView, DiNodeView


class DiUberGraphs:
    _node_dict_factory = IDDict
    _node_attr_dict_factory = IDDict
    _edge_dict_factory = IDDict
    _edge_attr_dict_factory = IDDict
    _net_attr_dict_factory = dict

    def __getstate__(self):
        """Function that allows pickling.

        Returns
        -------
        dict
            The keys label the hypergraph dict and the values
            are dictionaries from the DiHypergraph class.

        Notes
        -----
        This allows the python multiprocessing module to be used.

        """
        return {
            "_edge_uid": self._edge_uid,
            "_net_attr": self._net_attr,
            "_node": self._node,
            "_node_attr": self._node_attr,
            "_edge": self._edge,
            "_edge_attr": self._edge_attr,
        }

    def __getattr__(self, attr):
        stat = getattr(self.nodes, attr, None)
        word = "nodes"
        if stat is None:
            stat = getattr(self.edges, attr, None)
            word = "edges"
        if stat is None:
            word = None
            raise AttributeError(
                f"{attr} is not a method of DiHypergraph or a recognized DiNodeStat or DiEdgeStat"
            )

        def func(node=None, *args, **kwargs):
            val = stat(*args, **kwargs).asdict()
            return val if node is None else val[node]

        func.__doc__ = f"""Equivalent to DH.{word}.{attr}.asdict(). For accepted *args and
        **kwargs, see documentation of DH.{word}.{attr}."""

        return func

    def __setstate__(self, state):
        """Function that allows unpickling of a dihypergraph.

        Parameters
        ----------
        state
            The keys access the dictionary names the values are the
            dictionarys themselves from the DiHypergraph class.

        Notes
        -----
        This allows the python multiprocessing module to be used.
        """
        self._edge_uid = state["_edge_uid"]
        self._net_attr = state["_net_attr"]
        self._node = state["_node"]
        self._node_attr = state["_node_attr"]
        self._edge = state["_edge"]
        self._edge_attr = state["_edge_attr"]
        self._nodeview = DiNodeView(self)
        self._edgeview = DiEdgeView(self)

    def __init__(self, incoming_data=None, **attr):
        self._edge_uid = count()
        self._net_attr = self._net_attr_dict_factory()

        self._node = self._node_dict_factory()
        self._node_attr = self._node_attr_dict_factory()

        self._edge = self._edge_dict_factory()
        self._edge_attr = self._edge_attr_dict_factory()

        # self._nodeview = DiNodeView(self)
        """A :class:`~xgi.core.views.DiNodeView` of the directed hypergraph."""

        # self._edgeview = DiEdgeView(self)
        """An :class:`~xgi.core.views.DiEdgeView` of the directed hypergraph."""

        # if incoming_data is not None:
        # This import needs to happen when this function is called, not when it is
        # defined.  Otherwise, a circular import error would happen.
        # from ..convert import to_dihypergraph

        # to_dihypergraph(incoming_data, create_using=self)
        self._net_attr.update(attr)  # must be after convert

    def add_node(self, node, **attr):
        """Add one node with optional attributes.

        Parameters
        ----------
        node : node
            A node can be any hashable Python object except None.
        attr : keyword arguments, optional
            Set or change node attributes using key=value.

        See Also
        --------
        add_nodes_from

        Notes
        -----
        If node is already in the dihypergraph, its attributes are still updated.

        """
        if node not in self._node:
            self._node[node] = {"in": set(), "out": set()}
            self._node_attr[node] = self._node_attr_dict_factory()
        self._node_attr[node].update(attr)

    def add_edge(self, members: Iterable, idx=None, **attr):
        """Add one directed hyperedge. Supports nested 'edge-like' elements or
        iterable groups of nodes (flattens one level for node-groups).
        """
        # Validate top-level structure: must be (tail, head)
        if isinstance(members, (tuple, list)) and len(members) == 2:
            tail = members[0]
            head = members[1]
        else:
            raise TypeError("Directed edge must be a list or tuple of length 2!")

        uid = next(self._edge_uid) if idx is None else idx

        # check that uid is not present yet
        if uid in self._edge:
            warnings.warn(f"uid {uid} already exists, cannot add edge {members}")
            return

        self._edge[uid] = {"in": set(), "out": set()}

        def _is_edge_like(el):
            """Return True if el looks like a nested edge: (tail, head) with length 2
            and at least one side is an iterable (but not a string/bytes)."""
            if not isinstance(el, (list, tuple)) or len(el) != 2:
                return False
            a, b = el[0], el[1]
            a_is_iter = isinstance(a, Iterable) and not isinstance(a, (str, bytes))
            b_is_iter = isinstance(b, Iterable) and not isinstance(b, (str, bytes))
            return a_is_iter or b_is_iter

        def _process_element(el, is_tail=True):
            """Process one element from tail/head:
            - if edge-like -> recurse (add_edge)
            - elif iterable (but not str/bytes) -> iterate its items and treat them as nodes (flatten one level)
            - else: treat as single node
            """
            if _is_edge_like(el):
                # nested edge -> recurse
                self.add_edge(el)
                return

            # If it's an iterable of nodes (and not a string/bytes), flatten one level
            if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
                for sub in el:
                    # if a sub-element looks like a nested edge, allow recursion there too
                    if _is_edge_like(sub):
                        self.add_edge(sub)
                        continue
                    _add_node_to_edge(sub, is_tail)
                return

            # scalar node
            _add_node_to_edge(el, is_tail)

        def _add_node_to_edge(node, is_tail):
            """Add a scalar node to the graph and link it to uid."""
            if node not in self._node:
                self._node[node] = {"in": set(), "out": set()}
                self._node_attr[node] = self._node_attr_dict_factory()
            if is_tail:
                self._node[node]["out"].add(uid)
                self._edge[uid]["in"].add(node)
            else:
                self._node[node]["in"].add(uid)
                self._edge[uid]["out"].add(node)

        # Process tail elements
        # If tail itself is an iterable of nodes (which is typical), iterate it
        if isinstance(tail, Iterable) and not isinstance(tail, (str, bytes)):
            for el in tail:
                _process_element(el, is_tail=True)
        else:
            _process_element(tail, is_tail=True)

        # Process head elements
        if isinstance(head, Iterable) and not isinstance(head, (str, bytes)):
            for el in head:
                _process_element(el, is_tail=False)
        else:
            _process_element(head, is_tail=False)

        # Set attributes for this edge
        self._edge_attr[uid] = self._edge_attr_dict_factory()
        self._edge_attr[uid].update(attr)

        # If user provided idx, make sure internal uid counter stays consistent
        if idx is not None:
            update_uid_counter(self, idx)

            if isinstance(members, (tuple, list)) and len(members) == 2:
                tail = members[0]
                head = members[1]
            else:
                raise TypeError("Directed edge must be a list or tuple of length 2!")

            uid = next(self._edge_uid) if idx is None else idx

            # check that uid is not present yet
            if uid in self._edge:
                warnings.warn(f"uid {uid} already exists, cannot add edge {members}")
                return

            self._edge[uid] = {"in": set(), "out": set()}

            # helper that decides when an element is a nested edge vs a node
            def _is_edge_like(el):
                # edge-like = list/tuple of length 2 where at least one side is itself iterable
                return (
                    isinstance(el, (list, tuple))
                    and len(el) == 2
                    and (isinstance(el[0], Iterable) or isinstance(el[1], Iterable))
                )

            # process tail elements
            for element in tail:
                if _is_edge_like(element):
                    # element looks like a nested edge: treat it as an (tail, head) and add it
                    self.add_edge(element)
                    continue

                node = element

                if node not in self._node:
                    self._node[node] = {"in": set(), "out": set()}
                    self._node_attr[node] = self._node_attr_dict_factory()

                self._node[node]["out"].add(uid)
                self._edge[uid]["in"].add(node)

            # process head elements
            for element in head:
                if _is_edge_like(element):
                    self.add_edge(element)
                    continue

                node = element
                if node not in self._node:
                    self._node[node] = {"in": set(), "out": set()}
                    self._node_attr[node] = self._node_attr_dict_factory()

                self._node[node]["in"].add(uid)
                self._edge[uid]["out"].add(node)

            self._edge_attr[uid] = self._edge_attr_dict_factory()
            self._edge_attr[uid].update(attr)

            if idx is not None:  # set self._edge_uid correctly if user provided idx
                update_uid_counter(self, idx)
