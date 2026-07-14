"""
NumPy port of metrics.py.

get_dist_from_obj / get_wall_distance / dist_to_humans / dist_to_objects /
dist_to_walls / get_ttc are copied UNCHANGED from metrics.py: they already
operate on plain Python floats / shapely geometry, not torch tensors, so
there is nothing to port there. Shapely itself runs fine under Pyodide.

Only compute_metrics() and normalize_features() touched torch tensors --
those two are rewritten below using numpy, with identical logic/ordering.
"""
from shapely.geometry import Point, Polygon, LineString
from shapely.affinity import rotate, translate
import numpy as np
import math

EPS = 0.01
SOCIAL_SPACE_THRESHOLD = 0.4


# ---- unchanged geometry helpers (verbatim from metrics.py) ----

def get_dist_from_obj(object, o_x, o_y, o_angle, robot):
    o_shape = object['shape']['type']
    if o_shape == 'circle':
        o_length = object['shape']['length']
        object_shape = Point(o_x, o_y).buffer(o_length / 2)
    elif o_shape == 'rectangle':
        o_length = object['shape']['length']
        o_width = object['shape']['width']
        half_length, half_width = o_length / 2, o_width / 2
        rect = Polygon([
            (-half_length, -half_width),
            (half_length, -half_width),
            (half_length, half_width),
            (-half_length, half_width)
        ])
        rotated_rect = rotate(rect, o_angle, origin=(0, 0), use_radians=True)
        object_shape = translate(rotated_rect, xoff=o_x, yoff=o_y)
    else:
        raise ValueError("Invalid object shape. Must be 'circle' or 'rectangle'.")
    distance = robot.distance(object_shape)
    return distance


def get_wall_distance(r_x, r_y, r_radius, w_x1, w_y1, w_x2, w_y2):
    robot = Point(r_x, r_y).buffer(r_radius)
    wall = LineString([(w_x1, w_y1), (w_x2, w_y2)])
    distance = robot.distance(wall)
    return round(distance, 2)


def dist_to_humans(frame):
    r_x, r_y = frame['robot']['x'], frame['robot']['y']
    r_radius = frame['robot']['shape']['length'] / 2.
    h_radius = 0.3

    d_humans = []
    for human in frame['people']:
        h_x = human['x']
        h_y = human['y']
        dist_to_robot = max(0, math.sqrt((h_x - r_x) ** 2 + (h_y - r_y) ** 2) - (r_radius + h_radius))
        d_humans.append(dist_to_robot)

    return d_humans


def dist_to_objects(frame):
    r_x, r_y = frame['robot']['x'], frame['robot']['y']
    r_radius = frame['robot']['shape']['length'] / 2.

    robot = Point(r_x, r_y).buffer(r_radius)
    d_objects = []
    for obj in frame['objects']:
        o_x = obj['x']
        o_y = obj['y']
        o_angle = obj['angle']
        dist_to_robot = get_dist_from_obj(obj, o_x, o_y, o_angle, robot)
        d_objects.append(dist_to_robot)

    return d_objects


def dist_to_walls(frame, walls):
    r_x, r_y = frame['robot']['x'], frame['robot']['y']
    r_radius = frame['robot']['shape']['length'] / 2.

    d_walls = []
    for wall in walls:
        w_x1, w_y1 = wall[0], wall[1]
        w_x2, w_y2 = wall[2], wall[3]
        w_dist = get_wall_distance(r_x, r_y, r_radius, w_x1, w_y1, w_x2, w_y2)
        d_walls.append(w_dist)

    return d_walls


def get_ttc(cur_frame, prev_frame):
    robot_pose = np.array([cur_frame['robot']['x'], cur_frame['robot']['y']])
    time_diff = cur_frame['timestamp'] - prev_frame['timestamp']
    robot_pose_prev = np.array([prev_frame['robot']['x'], prev_frame['robot']['y']])
    if time_diff > 0:
        robot_vel = (robot_pose - robot_pose_prev) / time_diff
    else:
        robot_vel = np.array([0., 0.])
    human_radius = 0.3
    length = cur_frame['robot']['shape']['length']
    width = cur_frame['robot']['shape']['width']
    robot_radius = np.linalg.norm([length, width]) / 2

    radii_sum = human_radius + robot_radius
    radii_sum_sq = radii_sum * radii_sum

    calc_metrics = []
    for human in cur_frame['people']:
        ttc = -1
        cost_panic = -1
        cost_fear = -1
        C = np.array([human['x'], human['y']]) - robot_pose
        C_sq = C.dot(C)

        human_vel = np.array([0., 0.])
        for prev_human in prev_frame['people']:
            if prev_human['id'] == human['id']:
                pose_diff = np.array([human['x'] - prev_human['x'], human['y'] - prev_human['y']])
                if time_diff > 0:
                    human_vel = pose_diff / time_diff
                break

        if C_sq < radii_sum_sq:
            ttc = 0
        else:
            V = robot_vel - human_vel
            C_dot_V = C.dot(V)
            if C_dot_V > 0:
                V_sq = V.dot(V)
                f = (C_dot_V * C_dot_V) - (V_sq * (C_sq - radii_sum_sq))
                if f > 0:
                    ttc = (C_dot_V - np.sqrt(f)) / V_sq
                else:
                    g = np.sqrt(V_sq * C_sq - C_dot_V * C_dot_V)
                    if (g - (np.sqrt(V_sq) * radii_sum)) > EPS:
                        cost_panic = np.sqrt(V_sq / C_sq) * (g / (g - (np.sqrt(V_sq) * radii_sum)))

        if ttc > EPS:
            cost_fear = 1.0 / ttc
        elif ttc >= 0:
            cost_fear = 10.

        calc_metrics.append({'id': human['id'], 'ttc': ttc, 'fear': cost_fear, 'panic': cost_panic})

    return calc_metrics


# ---- numpy versions of the tensor-based functions ----

def compute_metrics(tDict_sequence):
    robot = tDict_sequence['robot']
    goal = tDict_sequence['goal']
    people = tDict_sequence['people']
    objects = tDict_sequence['objects']
    walls = tDict_sequence['walls']
    metrics_ft = tDict_sequence['metrics']

    dist_to_goal_pos = np.sqrt((robot['x'] - goal['x']) ** 2 + (robot['y'] - goal['y']) ** 2)
    angle_diff = robot['a'] - goal['a']
    dist_to_goal_angle = np.abs(np.arctan2(np.sin(angle_diff), np.cos(angle_diff)))

    success = np.logical_and(dist_to_goal_pos < goal['th_p'], dist_to_goal_angle < goal['th_a'])

    hum_exists = (np.sum(people['exists'], axis=1) > 0).astype(np.float64) if people['exists'].size else np.zeros(robot['x'].shape)
    wall_exists = np.full(robot['x'].shape, walls['x'].size > 0, dtype=np.float64)

    if people['exists'].size > 0:
        dist_human = np.where(people['exists'], metrics_ft['dist_human'], np.inf)
        dist_nearest_hum = np.min(dist_human, axis=1)
    else:
        dist_human = np.full((robot['x'].shape[0], 1), np.inf, dtype=np.float64)
        dist_nearest_hum = dist_human.squeeze(axis=1)

    if objects['exists'].size > 0:
        dist_nearest_object = np.min(np.where(objects['exists'], metrics_ft['dist_object'], np.inf), axis=1)
    else:
        dist_nearest_object = np.full(robot['x'].shape, np.inf, dtype=np.float64)

    inf_col = np.full((wall_exists.shape[0], 1), np.inf, dtype=np.float64)
    dist_wall = np.min(np.concatenate([metrics_ft['dist_walls'], inf_col], axis=1), axis=1)

    human_collision_flag = (dist_nearest_hum <= 0.).astype(np.float64)
    object_collision_flag = (dist_nearest_object <= 0.).astype(np.float64)
    wall_collision_flag = (dist_wall <= 0.).astype(np.float64)

    social_space_intrusionA = (dist_nearest_hum < SOCIAL_SPACE_THRESHOLD).astype(np.float64)
    num_near_humansA = np.sum(dist_human < SOCIAL_SPACE_THRESHOLD, axis=1).astype(np.float64)
    num_near_humansA2 = num_near_humansA ** 2

    social_space_intrusionB = (dist_nearest_hum < SOCIAL_SPACE_THRESHOLD * 1.5).astype(np.float64)
    num_near_humansB = np.sum(dist_human < SOCIAL_SPACE_THRESHOLD * 1.5, axis=1).astype(np.float64)
    num_near_humansB2 = num_near_humansB ** 2

    social_space_intrusionC = (dist_nearest_hum < SOCIAL_SPACE_THRESHOLD * 2.0).astype(np.float64)
    num_near_humansC = np.sum(dist_human < SOCIAL_SPACE_THRESHOLD * 2.0, axis=1).astype(np.float64)
    num_near_humansC2 = num_near_humansC ** 2

    if people['exists'].size > 0:
        valid_ttc = np.logical_and(people['exists'], metrics_ft['ttc'] >= 0.)
        ttc = np.where(valid_ttc, metrics_ft['ttc'], np.inf)
        min_ttc = np.min(ttc, axis=1)
        panic = np.where(np.logical_and(people['exists'], metrics_ft['panic'] >= 0), metrics_ft['panic'], 0.)
        max_panic = np.max(panic, axis=1)
        fear = np.where(np.logical_and(people['exists'], metrics_ft['fear'] >= 0), metrics_ft['fear'], 0.)
        max_fear = np.max(fear, axis=1)
    else:
        min_ttc = dist_human.squeeze(axis=1) if dist_human.ndim > 1 else dist_human
        max_panic = np.zeros(min_ttc.shape, dtype=np.float64)
        max_fear = np.zeros(min_ttc.shape, dtype=np.float64)

    global_dist_nearest_hum = np.minimum.accumulate(dist_nearest_hum)

    acum_dist_travelled = np.cumsum(robot['dist_travelled'])
    initial_dist_to_goal = np.full(dist_to_goal_pos.shape, dist_to_goal_pos[0], dtype=np.float64)
    with np.errstate(divide='ignore', invalid='ignore'):
        # first frame's acum_dist_travelled is 0 -> inf/nan, same as the
        # original torch code produces (silently) for that entry
        path_efficiency_ratio = np.clip(np.divide(initial_dist_to_goal, acum_dist_travelled), 0., 1.)

    step_ratio = tDict_sequence['indices'] / tDict_sequence['indices'][-1]
    episode_end = np.zeros(dist_to_goal_pos.shape, dtype=np.float64)
    episode_end[-1] = 1.

    cur_time = tDict_sequence['timestamp']
    prev_time = np.zeros(cur_time.shape, dtype=np.float64)
    prev_time[1:] = cur_time[:-1]
    prev_time[0] = prev_time[1] - 1
    prev_speed_x = np.zeros(robot['vx'].shape, dtype=np.float64)
    prev_speed_x[1:] = robot['vx'][:-1]
    prev_speed_x[0] = prev_speed_x[1]
    prev_speed_y = np.zeros(robot['vy'].shape, dtype=np.float64)
    prev_speed_y[1:] = robot['vy'][:-1]
    prev_speed_y[0] = prev_speed_y[1]

    diff_time = cur_time - prev_time
    acceleration_x = (robot['vx'] - prev_speed_x) / diff_time
    acceleration_y = (robot['vy'] - prev_speed_y) / diff_time

    tDict_sequence['robot']['acc_x'] = acceleration_x
    tDict_sequence['robot']['acc_y'] = acceleration_y

    metrics_dict = {
        'dist_to_goal_pos': dist_to_goal_pos,
        'dist_to_goal_angle': dist_to_goal_angle,
        'success': success,
        'hum_exists': hum_exists,
        'wall_exist': wall_exists,
        'dist_nearest_hum': dist_nearest_hum,
        'dist_nearest_object': dist_nearest_object,
        'dist_wall': dist_wall,
        'human_collision_flag': human_collision_flag,
        'object_collision_flag': object_collision_flag,
        'wall_collision_flag': wall_collision_flag,
        'social_space_intrusionA': social_space_intrusionA,
        'num_near_humansA': num_near_humansA,
        'num_near_humansA2': num_near_humansA2,
        'social_space_intrusionB': social_space_intrusionB,
        'num_near_humansB': num_near_humansB,
        'num_near_humansB2': num_near_humansB2,
        'social_space_intrusionC': social_space_intrusionC,
        'num_near_humansC': num_near_humansC,
        'num_near_humansC2': num_near_humansC2,
        'min_ttc': min_ttc,
        'min_ttc2': min_ttc ** 2,
        'max_fear': max_fear,
        'max_panic': max_panic,
        'global_dist_nearest_hum': global_dist_nearest_hum,
        'path_efficiency_ratio': path_efficiency_ratio,
        'step_ratio': step_ratio,
        'episode_end': episode_end,
    }

    tDict_sequence['computed_metrics'] = metrics_dict
    return tDict_sequence


def normalize_features(tDict_sequence, max_values):
    for key, value in list(tDict_sequence.items()):
        if key == 'robot':
            v = value
            r = tDict_sequence['robot']
            r['x'] = np.clip(v['x'], -max_values['scale'], max_values['scale']) / max_values['scale']
            r['y'] = np.clip(v['y'], -max_values['scale'], max_values['scale']) / max_values['scale']
            r['w'] = np.clip(v['w'], -max_values['scale'], max_values['scale']) / max_values['scale']
            r['l'] = np.clip(v['l'], -max_values['scale'], max_values['scale']) / max_values['scale']
            r['vx'] = np.clip(v['vx'], -max_values['max_v'], max_values['max_v']) / max_values['max_v']
            r['vy'] = np.clip(v['vy'], -max_values['max_v'], max_values['max_v']) / max_values['max_v']
            r['va'] = np.clip(v['va'], -max_values['max_va'], max_values['max_va']) / max_values['max_va']
            r['acc_x'] = np.clip(v['acc_x'], -max_values['max_acc'], max_values['max_acc']) / max_values['max_acc']
            r['acc_y'] = np.clip(v['acc_y'], -max_values['max_acc'], max_values['max_acc']) / max_values['max_acc']

        elif key == 'goal':
            g = tDict_sequence['goal']
            g['th_p'] = np.clip(value['th_p'], -max_values['scale'], max_values['scale']) / max_values['scale']
            max_th_a = max_values['max_va']
            g['th_a'] = np.clip(value['th_a'], -max_th_a, max_th_a) / max_th_a

        elif key in ['people', 'objects']:
            if value['x'].size == 0 or (value['x'].ndim > 1 and value['x'].shape[1] == 0):
                tDict_sequence[key]['x'] = value['x']
                tDict_sequence[key]['y'] = value['y']
                if key == 'objects':
                    tDict_sequence[key]['w'] = value['w']
                    tDict_sequence[key]['l'] = value['l']
            else:
                mask = value['exists']
                tDict_sequence[key]['x'] = np.where(mask, np.clip(value['x'], -max_values['scale'], max_values['scale']) / max_values['scale'], 0.0)
                tDict_sequence[key]['y'] = np.where(mask, np.clip(value['y'], -max_values['scale'], max_values['scale']) / max_values['scale'], 0.0)
                if key == 'objects':
                    tDict_sequence[key]['w'] = np.where(mask, np.clip(value['w'], -max_values['scale'], max_values['scale']) / max_values['scale'], 0.0)
                    tDict_sequence[key]['l'] = np.where(mask, np.clip(value['l'], -max_values['scale'], max_values['scale']) / max_values['scale'], 0.0)

        elif key == 'metrics':
            m = tDict_sequence['metrics']
            m['dist_human'] = np.clip(value['dist_human'], -max_values['scale'], max_values['scale']) / max_values['scale']
            m['dist_object'] = np.clip(value['dist_object'], -max_values['scale'], max_values['scale']) / max_values['scale']
            m['dist_walls'] = np.clip(value['dist_walls'], -max_values['scale'], max_values['scale']) / max_values['scale']

        elif key == 'computed_metrics':
            for metric_name in tDict_sequence['computed_metrics'].keys():
                max_val = max_values.get(metric_name)
                tDict_sequence[key][metric_name] = np.clip(tDict_sequence['computed_metrics'][metric_name], -max_val, max_val) / max_val

        elif key == 'walls':
            w = tDict_sequence['walls']
            w['x'] = np.clip(value['x'], -max_values['scale'], max_values['scale']) / max_values['scale']
            w['y'] = np.clip(value['y'], -max_values['scale'], max_values['scale']) / max_values['scale']

        elif key == 'context':
            for k in tDict_sequence['context'].keys():
                tDict_sequence['context'][k] = tDict_sequence['context'][k] / max_values['max_c']

    return tDict_sequence
