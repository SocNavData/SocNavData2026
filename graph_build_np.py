"""
NumPy port of the graph-construction pieces of datasetHomo.SocNavHomoDataset
that are needed for inference: set_all_features / _get_walls /
_structure_to_graph. No torch_geometric.data.Dataset/Data/Batch scaffolding
is used -- each frame is just a plain (node_feats, edge_index) numpy pair,
which is all HybridModelNumpy needs.

mirror_sequence(), collate(), and the Dataset/DataLoader machinery are
intentionally NOT ported: they exist for training-time batching and data
augmentation, not for evaluating a single trajectory.
"""
import math
import numpy as np


TYPE_FEATURES = ['robot', 'goal', 'human', 'object', 'wall']
ROBOT_FEATURES = ['r_x', 'r_y', 'r_sin_a', 'r_cos_a', 'dlin_gr', 'dang_gr', 'r_vx', 'r_vy',
                  'r_va', 'r_acc_x', 'r_acc_y', 'r_w', 'r_l']
GOAL_FEATURES = ['g_x', 'g_y', 'g_sin_a', 'g_cos_a', 'th_pos', 'th_angle']
HUMAN_FEATURES = ['h_x', 'h_y', 'h_sin_a', 'h_cos_a', 'dist_hr', 'dcenter_hr']
OBJECT_FEATURES = ['o_x', 'o_y', 'o_sin_a', 'o_cos_a', 'o_w', 'o_l', 'dist_or', 'dcenter_or']
WALL_FEATURES = ['w_x', 'w_y', 'w_sin_a', 'w_cos_a', 'w_w', 'w_l', 'dist_wr']

ALL_FEATURES = TYPE_FEATURES + ROBOT_FEATURES + GOAL_FEATURES + HUMAN_FEATURES + OBJECT_FEATURES + WALL_FEATURES
FEATURE_INDEX = {name: i for i, name in enumerate(ALL_FEATURES)}

# NOTE: modelHomo.py's robot node feature block sets r_vx/r_vy/r_va/r_acc_x/
# r_acc_y all as commented-out (dead) code in the original -- only r_w, r_l,
# dlin_gr, dang_gr are actually populated for the robot node. Mirrored
# faithfully below (i.e. those "unused" indices stay at 0, matching the
# original model exactly).

METRICS_FEATURES = ['dist_to_goal_pos', 'dist_to_goal_angle', 'success', 'hum_exists', 'wall_exist',
                     'dist_nearest_hum', 'dist_nearest_object', 'dist_wall', 'human_collision_flag',
                     'object_collision_flag', 'wall_collision_flag', 'social_space_intrusionA',
                     'num_near_humansA', 'num_near_humansA2', 'social_space_intrusionB',
                     'num_near_humansB', 'num_near_humansB2', 'social_space_instrusionC',
                     'num_near_humansC', 'num_near_humansC2', 'min_ttc', 'min_ttc2', 'max_fear',
                     'max_panic', 'global_dist_nearest_hum', 'path_efficiency_ratio', 'step_ratio',
                     'episode_end']

MAX_VALUES = {'scale': 10.0, 'max_v': 10.0, 'max_va': 2 * np.pi, 'max_acc': 3.0, 'max_c': 100.0,
              'dist_to_goal_pos': 10, 'dist_to_goal_angle': np.pi, 'success': 1, 'hum_exists': 1,
              'wall_exist': 1, 'dist_nearest_hum': 10, 'dist_nearest_object': 10, 'dist_wall': 10,
              'human_collision_flag': 1, 'object_collision_flag': 1, 'wall_collision_flag': 1,
              'social_space_intrusionA': 1, 'num_near_humansA': 10, 'num_near_humansA2': 10,
              'social_space_intrusionB': 1, 'num_near_humansB': 10, 'num_near_humansB2': 10,
              'social_space_intrusionC': 1, 'num_near_humansC': 10, 'num_near_humansC2': 10,
              'min_ttc': 10, 'min_ttc2': 100, 'max_fear': 10, 'max_panic': 10,
              'global_dist_nearest_hum': 10, 'path_efficiency_ratio': 1, 'step_ratio': 1,
              'episode_end': 1}


def _get_walls(walls):
    wall_points, id_walls, angle_walls, length_walls = [], [], [], []
    wx = walls['x']
    wy = walls['y']
    num_walls = len(wx) // 2

    for i in range(num_walls):
        x1, y1 = wx[2 * i], wy[2 * i]
        x2, y2 = wx[2 * i + 1], wy[2 * i + 1]
        dx, dy = x2 - x1, y2 - y1
        distance = (dx ** 2 + dy ** 2) ** 0.5
        angle = math.atan2(dy, dx) + math.pi / 2
        curr_x = (x1 + x2) / 2
        curr_y = (y1 + y2) / 2
        wall_points.append([curr_x, curr_y])
        id_walls.append(i)
        angle_walls.append(angle)
        length_walls.append(distance)

    return wall_points, id_walls, angle_walls, length_walls


def structure_to_graph(d, index):
    """d: the normalized tensor dict (numpy version, output of
    metrics_np.normalize_features). index: frame index within the trajectory.
    Returns (node_feats (N, F) float32, edge_index (2, E) int64, metrics_frame (M+C,) float32)."""
    num_node_features = len(ALL_FEATURES)
    graph_feats = []

    node_id = 0
    rx, ry = d['robot']['x'][index], d['robot']['y'][index]

    # robot node
    node_feats = np.zeros(num_node_features, dtype=np.float32)
    node_feats[FEATURE_INDEX['robot']] = 1.
    node_feats[FEATURE_INDEX['r_x']] = rx
    node_feats[FEATURE_INDEX['r_y']] = ry
    node_feats[FEATURE_INDEX['r_sin_a']] = math.sin(d['robot']['a'][index])
    node_feats[FEATURE_INDEX['r_cos_a']] = math.cos(d['robot']['a'][index])
    node_feats[FEATURE_INDEX['r_w']] = d['robot']['w'][index]
    node_feats[FEATURE_INDEX['r_l']] = d['robot']['l'][index]
    node_feats[FEATURE_INDEX['dlin_gr']] = d['computed_metrics']['dist_to_goal_pos'][index]
    node_feats[FEATURE_INDEX['dang_gr']] = d['computed_metrics']['dist_to_goal_angle'][index]
    graph_feats.append(node_feats)
    node_id += 1

    # goal node
    node_feats = np.zeros(num_node_features, dtype=np.float32)
    node_feats[FEATURE_INDEX['goal']] = 1.
    node_feats[FEATURE_INDEX['g_x']] = d['goal']['x'][index]
    node_feats[FEATURE_INDEX['g_y']] = d['goal']['y'][index]
    node_feats[FEATURE_INDEX['g_sin_a']] = math.sin(d['goal']['a'][index])
    node_feats[FEATURE_INDEX['g_cos_a']] = math.cos(d['goal']['a'][index])
    node_feats[FEATURE_INDEX['th_pos']] = d['goal']['th_p'][index]
    node_feats[FEATURE_INDEX['th_angle']] = d['goal']['th_a'][index]
    graph_feats.append(node_feats)
    node_id += 1

    # human nodes
    num_humans = d['people']['x'].shape[1] if d['people']['x'].size else 0
    people_exist = d['people']['exists']
    for i in range(num_humans):
        if people_exist[index, i]:
            node_id += 1
            node_feats = np.zeros(num_node_features, dtype=np.float32)
            px = d['people']['x'][index, i]
            py = d['people']['y'][index, i]
            pa = d['people']['a'][index, i]
            dist_to_robot = d['metrics']['dist_human'][index, i]
            dcenter_to_robot = math.sqrt((px - rx) ** 2 + (py - ry) ** 2)
            node_feats[FEATURE_INDEX['human']] = 1.
            node_feats[FEATURE_INDEX['h_x']] = px
            node_feats[FEATURE_INDEX['h_y']] = py
            node_feats[FEATURE_INDEX['h_sin_a']] = math.sin(pa)
            node_feats[FEATURE_INDEX['h_cos_a']] = math.cos(pa)
            node_feats[FEATURE_INDEX['dist_hr']] = dist_to_robot
            node_feats[FEATURE_INDEX['dcenter_hr']] = dcenter_to_robot
            graph_feats.append(node_feats)

    # object nodes
    num_objects = d['objects']['x'].shape[1] if d['objects']['x'].size else 0
    objects_exist = d['objects']['exists']
    for i in range(num_objects):
        if objects_exist[index, i]:
            node_id += 1
            node_feats = np.zeros(num_node_features, dtype=np.float32)
            ox = d['objects']['x'][index, i]
            oy = d['objects']['y'][index, i]
            oa = d['objects']['a'][index, i]
            dist_to_robot = d['metrics']['dist_object'][index, i]
            dcenter_to_robot = math.sqrt((ox - rx) ** 2 + (oy - ry) ** 2)
            node_feats[FEATURE_INDEX['object']] = 1.
            node_feats[FEATURE_INDEX['o_x']] = ox
            node_feats[FEATURE_INDEX['o_y']] = oy
            node_feats[FEATURE_INDEX['o_sin_a']] = math.sin(oa)
            node_feats[FEATURE_INDEX['o_cos_a']] = math.cos(oa)
            node_feats[FEATURE_INDEX['dist_or']] = dist_to_robot
            node_feats[FEATURE_INDEX['o_w']] = d['objects']['w'][index, i]
            node_feats[FEATURE_INDEX['o_l']] = d['objects']['l'][index, i]
            node_feats[FEATURE_INDEX['dcenter_or']] = dcenter_to_robot
            graph_feats.append(node_feats)

    # wall nodes
    walls = d['walls']
    if walls is not None and walls['x'].size > 0:
        raw_points, id_walls, a_walls, l_walls = _get_walls(walls)
        for pt, idW, wa, la in zip(raw_points, id_walls, a_walls, l_walls):
            node_id += 1
            node_feats = np.zeros(num_node_features, dtype=np.float32)
            wx_, wy_ = pt[0], pt[1]
            dist_to_robot = d['metrics']['dist_walls'][index, idW]
            node_feats[FEATURE_INDEX['wall']] = 1.
            node_feats[FEATURE_INDEX['w_x']] = wx_
            node_feats[FEATURE_INDEX['w_y']] = wy_
            node_feats[FEATURE_INDEX['w_sin_a']] = math.sin(wa)
            node_feats[FEATURE_INDEX['w_cos_a']] = math.cos(wa)
            node_feats[FEATURE_INDEX['dist_wr']] = dist_to_robot
            node_feats[FEATURE_INDEX['w_w']] = la
            node_feats[FEATURE_INDEX['w_l']] = 0.01
            graph_feats.append(node_feats)

    context_values = [d['context'][c_key][index] for c_key in d['context'].keys()]
    context_arr = np.array(context_values, dtype=np.float32)

    metrics_values = [d['computed_metrics'][m_key][index] for m_key in d['computed_metrics'].keys()]
    metrics_arr = np.array(metrics_values, dtype=np.float32)

    metrics_frame = np.concatenate([metrics_arr, context_arr]).astype(np.float32)

    node_feats_mat = np.stack(graph_feats, axis=0)
    num_nodes = node_feats_mat.shape[0]

    # star topology: every non-robot node connects (bidirectionally) to node 0
    list_N = np.arange(1, num_nodes)
    list_0 = np.zeros(num_nodes - 1, dtype=np.int64)
    edge_index = np.stack([
        np.concatenate([list_N, list_0]),
        np.concatenate([list_0, list_N]),
    ]).astype(np.int64)

    return node_feats_mat, edge_index, metrics_frame
