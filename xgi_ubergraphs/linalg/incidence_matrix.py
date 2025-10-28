import numpy as np
from scipy.sparse import csr_array

def incidence_matrix(
    H, order=None, sparse=True, index=False, weight=lambda node, edge, H: 1
):
    """A function to generate a weighted incidence matrix from a Hypergraph object,
    where the rows correspond to nodes and the columns correspond to edges.

    Parameters
    ----------
    H: Hypergraph object
        The hypergraph of interest
    order: int, optional
        Order of interactions to use. If None (default), all orders are used. If int,
        must be >= 1.
    sparse: bool, default: True
        Specifies whether the output matrix is a scipy sparse matrix or a numpy matrix
    index: bool, default: False
        Specifies whether to output dictionaries mapping the node and edge IDs to
        indices.
    weight: lambda function, default=lambda function outputting 1
        A function specifying the weight, given a node and edge

    Returns
    -------
    I: numpy.ndarray or scipy csr_array
        The incidence matrix, has dimension (n_nodes, n_edges)
    rowdict: dict
        The dictionary mapping indices to node IDs, if index is True
    coldict: dict
        The dictionary mapping indices to edge IDs, if index is True

    """
    node_ids = H.nodes
    edge_ids = H.edges

    if order is not None:
        edge_ids = H.edges.filterby("order", order)
    if not edge_ids or not node_ids:
        if sparse:
            Identity_Matrix = csr_array((0, 0), dtype=int)
        else:
            Identity_Matrix = np.empty((0, 0), dtype=int)
        return (Identity_Matrix, {}, {}) if index else Identity_Matrix

    num_edges = len(edge_ids)
    num_nodes = len(node_ids)

    node_dict = dict(zip(node_ids, range(num_nodes)))
    edge_dict = dict(zip(edge_ids, range(num_edges)))

    if index:
        rowdict = {v: k for k, v in node_dict.items()}
        coldict = {v: k for k, v in edge_dict.items()}

    # Compute the non-zero values, row and column indices for the given order
    rows = []
    cols = []
    data = []
    for edge in edge_ids:
        members = H._edge[edge]
        for node in members:
            rows.append(node_dict[node])
            cols.append(edge_dict[edge])
            data.append(weight(node, edge, H))

    # Create the incidence matrix as a CSR matrix
    if sparse:
        Identity_Matrix = csr_array((data, (rows, cols)), shape=(num_nodes, num_edges), dtype=int)
    else:
        Identity_Matrix = np.zeros((num_nodes, num_edges), dtype=int)
        Identity_Matrix[rows, cols] = data

    return (Identity_Matrix, rowdict, coldict) if index else Identity_Matrix