"""
Pure-NumPy re-implementation of torch.nn.GRU (batch_first=True), matching
PyTorch's exact gate equations and weight layout so state_dict weights can
be dropped in directly.
"""
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class NumpyGRU:
    def __init__(self, weights, num_layers, hidden_size):
        """
        weights: dict with keys 'weight_ih_l{k}', 'weight_hh_l{k}',
                 'bias_ih_l{k}', 'bias_hh_l{k}' for k in range(num_layers),
                 exactly as in torch.nn.GRU.state_dict() (dropout is a
                 no-op at eval time, so it's ignored here).
        """
        self.num_layers = num_layers
        self.hidden_size = hidden_size
        self.weights = {k: np.asarray(v) for k, v in weights.items()}

    def _layer_forward(self, x, layer):
        """x: (B, T, F_in) -> returns (B, T, H) full sequence of hidden states."""
        W_ih = self.weights[f'weight_ih_l{layer}']   # (3H, F_in)
        W_hh = self.weights[f'weight_hh_l{layer}']    # (3H, H)
        b_ih = self.weights[f'bias_ih_l{layer}']      # (3H,)
        b_hh = self.weights[f'bias_hh_l{layer}']      # (3H,)

        B, T, _ = x.shape
        H = self.hidden_size
        h = np.zeros((B, H), dtype=x.dtype)
        outputs = np.zeros((B, T, H), dtype=x.dtype)

        # split gate blocks: PyTorch order is [reset, update, new]
        W_ir, W_iz, W_in = W_ih[0:H], W_ih[H:2*H], W_ih[2*H:3*H]
        W_hr, W_hz, W_hn = W_hh[0:H], W_hh[H:2*H], W_hh[2*H:3*H]
        b_ir, b_iz, b_in = b_ih[0:H], b_ih[H:2*H], b_ih[2*H:3*H]
        b_hr, b_hz, b_hn = b_hh[0:H], b_hh[H:2*H], b_hh[2*H:3*H]

        for t in range(T):
            xt = x[:, t, :]
            r = sigmoid(xt @ W_ir.T + b_ir + h @ W_hr.T + b_hr)
            z = sigmoid(xt @ W_iz.T + b_iz + h @ W_hz.T + b_hz)
            n = np.tanh(xt @ W_in.T + b_in + r * (h @ W_hn.T + b_hn))
            h = (1 - z) * n + z * h
            outputs[:, t, :] = h

        return outputs

    def __call__(self, x):
        """x: (B, T, F_in) -> full sequence output of the last layer, (B, T, H)."""
        out = x
        for layer in range(self.num_layers):
            out = self._layer_forward(out, layer)
        return out
