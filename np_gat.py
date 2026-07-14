"""
Pure-NumPy re-implementation of torch_geometric.nn.GATConv (v1 attention),
matching PyG's default settings used in modelHomo.py:
    heads=H, concat=<bool>, negative_slope=0.2, add_self_loops=True,
    fill_value='mean', bias=True, residual=False, edge_dim=None.

Generic over edge_index (works for any graph, not just the star topology),
so it stays correct even if the graph construction changes later.
"""
import numpy as np


def leaky_relu(x, negative_slope=0.2):
    return np.where(x >= 0, x, x * negative_slope)


def softmax_by_group(scores, group_index, num_groups):
    """Softmax `scores` (E,) within each group defined by group_index (E,) in [0, num_groups)."""
    out = np.zeros_like(scores)
    # subtract per-group max for numerical stability
    group_max = np.full(num_groups, -np.inf, dtype=scores.dtype)
    np.maximum.at(group_max, group_index, scores)
    shifted = scores - group_max[group_index]
    exp = np.exp(shifted)
    group_sum = np.zeros(num_groups, dtype=scores.dtype)
    np.add.at(group_sum, group_index, exp)
    out = exp / group_sum[group_index]
    return out


def add_self_loops_mean_fill(edge_index, num_nodes):
    """Mirror PyG's add_self_loops(fill_value='mean') for the no-edge-attr case:
    just appends one self-loop edge per node (fill_value only matters for edge
    attributes, which we don't use here)."""
    src, dst = edge_index
    loop = np.arange(num_nodes)
    new_src = np.concatenate([src, loop])
    new_dst = np.concatenate([dst, loop])
    return np.stack([new_src, new_dst], axis=0)


class NumpyGATConv:
    def __init__(self, lin_weight, att_src, att_dst, bias, heads, concat,
                 negative_slope=0.2, add_self_loops=True):
        """
        lin_weight: (heads*out_channels, in_channels)  -- PyG's `lin.weight`
        att_src, att_dst: (1, heads, out_channels)
        bias: (out_channels,) if concat=False else (heads*out_channels,)
        """
        self.W = np.asarray(lin_weight)          # (H*C, F_in)
        self.att_src = np.asarray(att_src)[0]     # (H, C)
        self.att_dst = np.asarray(att_dst)[0]     # (H, C)
        self.bias = np.asarray(bias)
        self.heads = heads
        self.concat = concat
        self.negative_slope = negative_slope
        self.add_self_loops = add_self_loops
        self.out_channels = self.att_src.shape[1]

    def __call__(self, x, edge_index):
        """
        x: (N, F_in) numpy array
        edge_index: (2, E) numpy int array, row0=src, row1=dst
        returns: (N, out_channels) if concat=False else (N, heads*out_channels)
        """
        N = x.shape[0]
        H, C = self.heads, self.out_channels

        if self.add_self_loops:
            edge_index = add_self_loops_mean_fill(edge_index, N)

        src, dst = edge_index[0], edge_index[1]

        # linear transform: (N, H*C) -> (N, H, C)
        x_lin = x @ self.W.T
        x_lin = x_lin.reshape(N, H, C)

        alpha_src_node = np.einsum('nhc,hc->nh', x_lin, self.att_src)  # (N,H)
        alpha_dst_node = np.einsum('nhc,hc->nh', x_lin, self.att_dst)  # (N,H)

        # per-edge, per-head attention logits
        e = alpha_src_node[src] + alpha_dst_node[dst]   # (E,H)
        e = leaky_relu(e, self.negative_slope)

        # softmax over incoming edges of each destination node, per head
        alpha = np.zeros_like(e)
        for h in range(H):
            alpha[:, h] = softmax_by_group(e[:, h], dst, N)

        # weighted aggregation of source features into destination nodes
        out = np.zeros((N, H, C), dtype=x.dtype)
        contrib = x_lin[src] * alpha[:, :, None]   # (E,H,C)
        np.add.at(out, dst, contrib)

        if self.concat:
            out = out.reshape(N, H * C)
        else:
            out = out.mean(axis=1)

        out = out + self.bias
        return out
