"""
Pure-NumPy re-implementation of modelHomo.GNNModel + modelHomo.HybridModel
forward pass (inference only -- no autograd, no dropout).

This is meant to be loaded with weights produced by export_weights.py
(run once, offline, in a normal Python+torch environment) and then run
inside Pyodide/PyScript with only numpy as a dependency.
"""
import numpy as np

from np_gat import NumpyGATConv, leaky_relu
from np_gru import NumpyGRU


def linear(x, weight, bias):
    return x @ weight.T + bias


def layer_norm(x, weight, bias, eps=1e-5):
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    x_norm = (x - mean) / np.sqrt(var + eps)
    return x_norm * weight + bias


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class GNNModelNumpy:
    """Mirrors modelHomo.GNNModel. Note: the per-layer `layers_lin` residual
    branch in the original is defined but never applied in forward() (it's
    commented out), so those weights are loaded but intentionally unused."""

    def __init__(self, layer_weights, heads_list, concat):
        """
        layer_weights: list of dicts, one per GATConv layer, each with keys
                       'lin.weight', 'att_src', 'att_dst', 'bias'
        heads_list: list of head counts, one per layer
        concat: the gnn_concat bool used for every layer except the last
                (last layer is always heads=1, concat=False, matching
                modelHomo.GNNModel's construction)
        """
        self.layers = []
        n = len(layer_weights)
        for i, (w, heads) in enumerate(zip(layer_weights, heads_list)):
            is_last = (i == n - 1)
            layer_concat = False if is_last else concat
            self.layers.append(NumpyGATConv(
                np.array(w['lin.weight'], dtype=np.float32),
                np.array(w['att_src'], dtype=np.float32),
                np.array(w['att_dst'], dtype=np.float32),
                np.array(w['bias'], dtype=np.float32),
                heads=heads, concat=layer_concat,
            ))

    def __call__(self, x, edge_index):
        for i, layer in enumerate(self.layers):
            x = layer(x, edge_index)
            if i < len(self.layers) - 1:
                x = leaky_relu(x, negative_slope=0.1)
        return x


class HybridModelNumpy:
    """Mirrors modelHomo.HybridModel.forward for a single trajectory
    (batch size 1), which is the only case needed for interactive
    browser inference."""

    def __init__(self, weights, config):
        """
        weights: flat dict as produced by export_weights.py
        config: dict with keys: gnn_heads (list[int]), gnn_concat (bool),
                num_layers (rnn layers), rnn_hidden, context_vars,
                metrics_vars, gnn_output, only_gnn, only_metrics,
                rnn_activation ('sigmoid'|'tanh'|'linear'),
                num_linear_layers (int)
        """
        self.cfg = config
        self.only_gnn = config['only_gnn']
        self.only_metrics = config['only_metrics']
        self.context_vars = config['context_vars']
        self.metrics_vars = config['metrics_vars']

        def arr(x):
            return np.array(x, dtype=np.float32)

        gnn_layer_weights = weights['gnn_layers']
        self.gnn_block = GNNModelNumpy(gnn_layer_weights, config['gnn_heads'], config['gnn_concat'])

        self.contextNorm_w = arr(weights['contextNorm.weight'])
        self.contextNorm_b = arr(weights['contextNorm.bias'])

        if not self.only_gnn:
            self.metricsNorm_w = arr(weights['metricsNorm.weight'])
            self.metricsNorm_b = arr(weights['metricsNorm.bias'])
        if not self.only_metrics:
            self.gnnNorm_w = arr(weights['gnnNorm.weight'])
            self.gnnNorm_b = arr(weights['gnnNorm.bias'])

        rnn_weights = {k: arr(v) for k, v in weights['rnn'].items()}
        self.gru = NumpyGRU(rnn_weights, num_layers=config['num_layers'],
                             hidden_size=config['rnn_hidden'])

        self.fc_layers = [(arr(w), arr(b)) for (w, b) in weights['fc_layers']]
        self.activation = config['rnn_activation']

    def forward(self, node_feats_seq, edge_index_seq, metrics_seq_2d):
        """
        node_feats_seq: list of length T, each (num_nodes_t, F) numpy array
                        (node 0 is always the robot node)
        edge_index_seq: list of length T, each (2, E_t) numpy int array
        metrics_seq_2d: (T, metrics_vars + context_vars) numpy array, in the
                         same column order as SocNavHomoDataset produces
                         (metrics first, context last)
        returns: python float, the predicted reward
        """
        T = len(node_feats_seq)

        if not self.only_metrics:
            frame_vecs = []
            for x, edge_index in zip(node_feats_seq, edge_index_seq):
                gnn_out = self.gnn_block(x, edge_index)
                frame_vecs.append(gnn_out[0])  # robot node is index 0
            x_seq = np.stack(frame_vecs, axis=0)  # (T, gnn_output)
            x_seq = layer_norm(x_seq, self.gnnNorm_w, self.gnnNorm_b)

        metrics_part = metrics_seq_2d[:, :self.metrics_vars]
        context_part = metrics_seq_2d[:, -self.context_vars:] if self.context_vars > 0 else metrics_seq_2d[:, 0:0]
        context_norm = layer_norm(context_part, self.contextNorm_w, self.contextNorm_b)

        if self.only_metrics:
            metrics_norm = layer_norm(metrics_part, self.metricsNorm_w, self.metricsNorm_b)
            seq = np.concatenate([metrics_norm, context_norm], axis=1)
        elif self.only_gnn:
            seq = np.concatenate([x_seq, context_norm], axis=1)
        else:
            metrics_norm = layer_norm(metrics_part, self.metricsNorm_w, self.metricsNorm_b)
            seq = np.concatenate([x_seq, metrics_norm, context_norm], axis=1)

        seq_batch = seq[None, :, :]  # (1, T, F) -- batch size 1
        rnn_out = self.gru(seq_batch)  # (1, T, H)
        out = rnn_out[0, T - 1, :]  # last valid timestep

        if self.context_vars > 0:
            out = np.concatenate([out, context_part[0]], axis=0)

        for (w, b) in self.fc_layers[:-1]:
            out = linear(out, w, b)
            out = leaky_relu(out, negative_slope=0.01)  # nn.LeakyReLU default
        w, b = self.fc_layers[-1]
        out = linear(out, w, b)

        if self.activation == 'sigmoid':
            out = sigmoid(out)
        elif self.activation == 'tanh':
            out = np.tanh(out)
            out = (out + 1.0) / 2.0

        return float(out[0])
