"""
NumPy port of data_conversions.py.

Only sequence_to_tensor() is ported: it's the only function on the
inference path (compute_reward -> SocNavHomoDataset.process_structure).
tensor_to_sequence() and clone_sequence() are only used for the training-time
data-augmentation (mirroring) path and aren't needed to *evaluate* a
trajectory, so they're intentionally left out of the browser port.
"""
import math
import numpy as np

import metrics_np as metrics


def sequence_to_tensor(data, frame_threshold, context):
    sequence = data['sequence']
    last_i = len(sequence) - 1
    robot = {'x': [], 'y': [], 'a': [], 'vx': [], 'vy': [], 'va': [], 'w': [], 'l': []}
    goal = {'x': [], 'y': [], 'a': [], 'th_p': [], 'th_a': []}
    people = {'x': [], 'y': [], 'a': []}
    objects = {'x': [], 'y': [], 'a': [], 'w': [], 'l': []}
    metrics_ft = {'dist_human': [], 'ttc': [], 'panic': [], 'fear': [], 'dist_object': [],
                  'dist_walls': []}
    filtered_sequence = []
    last_timestamp = -float('inf')
    prev_index = 0

    for i, frame in enumerate(sequence):
        current_timestamp = frame['timestamp']
        if current_timestamp - last_timestamp >= frame_threshold or i == last_i:
            if i == 0:
                inm_prev_frame = frame
                inm_prev_timestamp = -float('inf')
            else:
                inm_prev_frame = sequence[prev_index]
                inm_prev_timestamp = sequence[prev_index]['timestamp']
            prev_frame = sequence[prev_index]
            prev_index = i
            diff_time = current_timestamp - inm_prev_timestamp
            people_list = {}
            people_list['id'] = [p['id'] for p in frame['people']]
            people_list['x'] = [p['x'] for p in frame['people']]
            people_list['y'] = [p['y'] for p in frame['people']]
            people_list['a'] = [p['angle'] for p in frame['people']]
            objects_list = {}
            objects_list['x'] = [o['x'] for o in frame['objects']]
            objects_list['y'] = [o['y'] for o in frame['objects']]
            objects_list['a'] = [o['angle'] for o in frame['objects']]
            objects_list['w'] = [o['shape']['width'] for o in frame['objects']]
            objects_list['l'] = [o['shape']['length'] for o in frame['objects']]
            objects_list['shape'] = [o['shape']['type'] for o in frame['objects']]
            objects_list['type'] = [o['type'] for o in frame['objects']]
            r_x, r_y = frame['robot']['x'], frame['robot']['y']
            cur_ttc = metrics.get_ttc(frame, prev_frame)
            d_humans = metrics.dist_to_humans(frame)
            d_objects = metrics.dist_to_objects(frame)
            d_walls = metrics.dist_to_walls(frame, data['walls'])
            frame['people_list'] = people_list
            frame['objects_list'] = objects_list
            frame['ttc'] = [m['ttc'] for m in cur_ttc]
            frame['panic'] = [m['panic'] for m in cur_ttc]
            frame['fear'] = [m['fear'] for m in cur_ttc]
            frame['dist_human'] = d_humans
            frame['dist_object'] = d_objects
            frame['dist_wall'] = d_walls
            diff_angle = frame['robot']['angle'] - inm_prev_frame['robot']['angle']
            frame['robot_vx'] = (r_x - inm_prev_frame['robot']['x']) / diff_time
            frame['robot_vy'] = (r_y - inm_prev_frame['robot']['y']) / diff_time
            frame['robot_va'] = (math.atan2(math.sin(diff_angle), math.cos(diff_angle))) / diff_time
            frame['dist_travelled'] = math.sqrt((r_x - prev_frame['robot']['x']) ** 2 +
                                                 (r_y - prev_frame['robot']['y']) ** 2)
            frame['index'] = i
            last_timestamp = current_timestamp
            filtered_sequence.append(frame)

    timestamp = np.array([f['timestamp'] for f in filtered_sequence], dtype=np.float64)
    indices = np.array([f['index'] for f in filtered_sequence], dtype=np.float64)
    robot['x'] = np.array([f['robot']['x'] for f in filtered_sequence], dtype=np.float64)
    robot['y'] = np.array([f['robot']['y'] for f in filtered_sequence], dtype=np.float64)
    robot['a'] = np.array([f['robot']['angle'] for f in filtered_sequence], dtype=np.float64)
    robot['vx'] = np.array([f['robot_vx'] for f in filtered_sequence], dtype=np.float64)
    robot['vy'] = np.array([f['robot_vy'] for f in filtered_sequence], dtype=np.float64)
    robot['va'] = np.array([f['robot_va'] for f in filtered_sequence], dtype=np.float64)
    robot['w'] = np.array([f['robot']['shape']['width'] for f in filtered_sequence], dtype=np.float64)
    robot['l'] = np.array([f['robot']['shape']['length'] for f in filtered_sequence], dtype=np.float64)
    robot['dist_travelled'] = np.array([f['dist_travelled'] for f in filtered_sequence], dtype=np.float64)
    goal['x'] = np.array([f['goal']['x'] for f in filtered_sequence], dtype=np.float64)
    goal['y'] = np.array([f['goal']['y'] for f in filtered_sequence], dtype=np.float64)
    goal['a'] = np.array([f['goal']['angle'] for f in filtered_sequence], dtype=np.float64)
    goal['th_p'] = np.array([f['goal']['pos_threshold'] + 0.1 for f in filtered_sequence], dtype=np.float64)
    goal['th_a'] = np.array([f['goal']['angle_threshold'] for f in filtered_sequence], dtype=np.float64)

    max_people = max(len(frame['people_list']['x']) for frame in filtered_sequence)
    pmask_list, id_list, x_list, y_list, a_list = [], [], [], [], []
    drobot_list, ttc_list, panic_list, fear_list = [], [], [], []
    for f in filtered_sequence:
        people_id = f['people_list']['id']
        people_x = f['people_list']['x']
        people_y = f['people_list']['y']
        people_a = f['people_list']['a']
        people_dist = f['dist_human']
        ttc = f['ttc']
        panic = f['panic']
        fear = f['fear']
        n_people = len(people_x)
        pmask_list.append(np.array([True] * n_people + [False] * (max_people - n_people)))
        if n_people < max_people:
            people_id = people_id + [0.] * (max_people - n_people)
            people_x = people_x + [0.] * (max_people - n_people)
            people_y = people_y + [0.] * (max_people - n_people)
            people_a = people_a + [0.] * (max_people - n_people)
            people_dist = people_dist + [0.] * (max_people - n_people)
            ttc = ttc + [0.] * (max_people - n_people)
            panic = panic + [0.] * (max_people - n_people)
            fear = fear + [0.] * (max_people - n_people)
        id_list.append(people_id)
        x_list.append(np.array(people_x, dtype=np.float64))
        y_list.append(np.array(people_y, dtype=np.float64))
        a_list.append(np.array(people_a, dtype=np.float64))
        drobot_list.append(np.array(people_dist, dtype=np.float64))
        ttc_list.append(np.array(ttc, dtype=np.float64))
        panic_list.append(np.array(panic, dtype=np.float64))
        fear_list.append(np.array(fear, dtype=np.float64))
    people['id'] = id_list
    people['x'] = np.stack(x_list, 0)
    people['y'] = np.stack(y_list, 0)
    people['a'] = np.stack(a_list, 0)
    people['exists'] = np.stack(pmask_list, 0)
    metrics_ft['dist_human'] = np.stack(drobot_list, 0)
    metrics_ft['ttc'] = np.stack(ttc_list, 0)
    metrics_ft['panic'] = np.stack(panic_list, 0)
    metrics_ft['fear'] = np.stack(fear_list, 0)

    max_objects = max(len(frame['objects_list']['x']) for frame in filtered_sequence)
    omask_list, x_list, y_list, a_list, w_list, l_list = [], [], [], [], [], []
    shape_list, type_list, drobot_list = [], [], []
    for f in filtered_sequence:
        objects_x = f['objects_list']['x']
        objects_y = f['objects_list']['y']
        objects_a = f['objects_list']['a']
        objects_w = f['objects_list']['w']
        objects_l = f['objects_list']['l']
        objects_shape = f['objects_list']['shape']
        objects_type = f['objects_list']['type']
        object_dist = f['dist_object']
        n_objects = len(objects_x)
        omask_list.append(np.array([True] * n_objects + [False] * (max_objects - n_objects)))
        if n_objects < max_objects:
            objects_x = objects_x + [0.] * (max_objects - n_objects)
            objects_y = objects_y + [0.] * (max_objects - n_objects)
            objects_a = objects_a + [0.] * (max_objects - n_objects)
            objects_w = objects_w + [0.] * (max_objects - n_objects)
            objects_l = objects_l + [0.] * (max_objects - n_objects)
            objects_shape = objects_shape + ['none'] * (max_objects - n_objects)
            objects_type = objects_type + ['none'] * (max_objects - n_objects)
            object_dist = object_dist + [0.] * (max_objects - n_objects)

        x_list.append(np.array(objects_x, dtype=np.float64))
        y_list.append(np.array(objects_y, dtype=np.float64))
        a_list.append(np.array(objects_a, dtype=np.float64))
        w_list.append(np.array(objects_w, dtype=np.float64))
        l_list.append(np.array(objects_l, dtype=np.float64))
        shape_list.append(objects_shape)
        type_list.append(objects_type)
        drobot_list.append(np.array(object_dist, dtype=np.float64))

    objects['x'] = np.stack(x_list, 0)
    objects['y'] = np.stack(y_list, 0)
    objects['a'] = np.stack(a_list, 0)
    objects['w'] = np.stack(w_list, 0)
    objects['l'] = np.stack(l_list, 0)
    objects['shape'] = shape_list
    objects['type'] = type_list
    objects['exists'] = np.stack(omask_list)
    metrics_ft['dist_object'] = np.stack(drobot_list)

    wallsX_list, wallsY_list = [], []
    for w in data['walls']:
        wallsX_list.append(w[0])
        wallsX_list.append(w[2])
        wallsY_list.append(w[1])
        wallsY_list.append(w[3])
    walls_x = np.array(wallsX_list, dtype=np.float64)
    walls_y = np.array(wallsY_list, dtype=np.float64)

    walls = {'x': walls_x, 'y': walls_y}
    drobot_list = []
    for frame in filtered_sequence:
        d_walls = np.array(frame['dist_wall'], dtype=np.float64)
        drobot_list.append(d_walls)
    metrics_ft['dist_walls'] = np.stack(drobot_list)

    context_ft = {}
    for var in context:
        context_ft[var] = np.full(robot['x'].shape, context[var], dtype=np.float64)

    tensor_dict = {'timestamp': timestamp,
                   'indices': indices,
                   'robot': robot,
                   'goal': goal,
                   'people': people,
                   'objects': objects,
                   'walls': walls,
                   'metrics': metrics_ft,
                   'context': context_ft}

    return tensor_dict, len(filtered_sequence)
