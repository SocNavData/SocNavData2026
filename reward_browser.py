"""
Drop-in, torch-free replacement for sn26gnn.Reward, built entirely on
numpy + shapely (both available in Pyodide/PyScript). Runs identically in
a normal Python interpreter or inside a browser via PyScript.

Prerequisites (produced once, offline, with the original torch environment):
    python export_weights.py gnn_gru_model.pytorch weights.json
    python export_context_csv.py anthropic_claude_context.csv context.json

Usage (same shape as the original sn26gnn.Reward):
    reward_model = Reward("weights.json", "context.json")
    score = reward_model.compute_reward(trajectory_dict, context_description)
"""
import json

import data_conversions_np as data_conversions
import data_normalization_np as data_normalization
import metrics_np as metrics
import graph_build_np as graph_build
from np_model import HybridModelNumpy


class Reward:
    def __init__(self, weights_path="weights.json", context_path="context.json"):
        with open(weights_path) as f:
            bundle = json.load(f)
        self.config = bundle["config"]
        self.model = HybridModelNumpy(bundle["weights"], self.config)

        with open(context_path) as f:
            self.context_table = json.load(f)

        self.frame_threshold = self.config.get("frame_threshold", 0.1)
        self.max_values = graph_build.MAX_VALUES

    def compute_reward(self, trajectory, context_description):
        """
        trajectory: dict with 'sequence' (list of frames) and 'walls',
                    exactly the same shape main.py loads from JSON.
        context_description: string, must match a row in the context CSV
                              (same lookup semantics as the original
                              SocNavHomoDataset: `.rstrip()`-normalized).
        returns: float reward
        """
        context_key = context_description.rstrip()
        if context_key not in self.context_table:
            raise KeyError(f"Unknown context description: {context_description!r}")
        context = self.context_table[context_key]

        tensor_dict, length = data_conversions.sequence_to_tensor(
            trajectory, self.frame_threshold, context)
        tensor_dict = data_normalization.tensor_transform_to_goal_fr(tensor_dict)
        tensor_dict = metrics.compute_metrics(tensor_dict)
        tensor_dict = metrics.normalize_features(tensor_dict, self.max_values)

        node_feats_seq = []
        edge_index_seq = []
        metrics_frames = []
        for i in range(length):
            node_feats, edge_index, metrics_frame = graph_build.structure_to_graph(tensor_dict, i)
            node_feats_seq.append(node_feats)
            edge_index_seq.append(edge_index)
            metrics_frames.append(metrics_frame)

        import numpy as np
        metrics_seq_2d = np.stack(metrics_frames, axis=0)

        return self.model.forward(node_feats_seq, edge_index_seq, metrics_seq_2d)
