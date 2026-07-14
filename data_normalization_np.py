import numpy as np


def tensor_transform_to_goal_fr(tDict_sequence):
    gx = tDict_sequence['goal']['x']
    gy = tDict_sequence['goal']['y']
    ga = tDict_sequence['goal']['a']
    sin_theta = np.sin(-ga)
    cos_theta = np.cos(-ga)

    rx = tDict_sequence['robot']['x']
    ry = tDict_sequence['robot']['y']
    ra = tDict_sequence['robot']['a']
    vx = tDict_sequence['robot']['vx']
    vy = tDict_sequence['robot']['vy']
    dx = rx - gx
    dy = ry - gy
    new_rx = dx * cos_theta - dy * sin_theta
    new_ry = dx * sin_theta + dy * cos_theta
    new_ra = np.arctan2(np.sin(ra - ga), np.cos(ra - ga))
    new_vx = vx * cos_theta - vy * sin_theta
    new_vy = vx * sin_theta + vy * cos_theta

    robot = {}
    robot['x'] = new_rx
    robot['y'] = new_ry
    robot['a'] = new_ra
    robot['vx'] = new_vx
    robot['vy'] = new_vy
    robot['va'] = tDict_sequence['robot']['va']
    robot['w'] = tDict_sequence['robot']['w']
    robot['l'] = tDict_sequence['robot']['l']
    robot['dist_travelled'] = tDict_sequence['robot']['dist_travelled']

    if tDict_sequence['people']['exists'].size > 0:
        px = tDict_sequence['people']['x']
        py = tDict_sequence['people']['y']
        pa = tDict_sequence['people']['a']
        gx2d = np.repeat(gx[:, None], px.shape[1], axis=1)
        gy2d = np.repeat(gy[:, None], px.shape[1], axis=1)
        ga2d = np.repeat(ga[:, None], px.shape[1], axis=1)
        sin_theta2d = np.repeat(sin_theta[:, None], px.shape[1], axis=1)
        cos_theta2d = np.repeat(cos_theta[:, None], px.shape[1], axis=1)
        dx = px - gx2d
        dy = py - gy2d
        new_px = dx * cos_theta2d - dy * sin_theta2d
        new_py = dx * sin_theta2d + dy * cos_theta2d
        new_pa = np.arctan2(np.sin(pa - ga2d), np.cos(pa - ga2d))

        people = {}
        people['x'] = new_px
        people['y'] = new_py
        people['a'] = new_pa
        people['id'] = tDict_sequence['people']['id']
        people['exists'] = tDict_sequence['people']['exists']
    else:
        people = tDict_sequence['people']

    if tDict_sequence['objects']['exists'].size > 0:
        ox = tDict_sequence['objects']['x']
        oy = tDict_sequence['objects']['y']
        oa = tDict_sequence['objects']['a']
        gx2d = np.repeat(gx[:, None], ox.shape[1], axis=1)
        gy2d = np.repeat(gy[:, None], ox.shape[1], axis=1)
        ga2d = np.repeat(ga[:, None], ox.shape[1], axis=1)
        sin_theta2d = np.repeat(sin_theta[:, None], ox.shape[1], axis=1)
        cos_theta2d = np.repeat(cos_theta[:, None], ox.shape[1], axis=1)
        dx = ox - gx2d
        dy = oy - gy2d
        new_ox = dx * cos_theta2d - dy * sin_theta2d
        new_oy = dx * sin_theta2d + dy * cos_theta2d
        new_oa = np.arctan2(np.sin(oa - ga2d), np.cos(oa - ga2d))

        objects = {}
        objects['x'] = new_ox
        objects['y'] = new_oy
        objects['a'] = new_oa
        objects['w'] = tDict_sequence['objects']['w']
        objects['l'] = tDict_sequence['objects']['l']
        objects['shape'] = tDict_sequence['objects']['shape']
        objects['type'] = tDict_sequence['objects']['type']
        objects['exists'] = tDict_sequence['objects']['exists']
    else:
        objects = tDict_sequence['objects']

    if tDict_sequence['walls']['x'].size > 0:
        wx = tDict_sequence['walls']['x']
        wy = tDict_sequence['walls']['y']
        gx2d = np.repeat(gx[:, None], wx.shape[0], axis=1)
        gy2d = np.repeat(gy[:, None], wx.shape[0], axis=1)
        sin_theta2d = np.repeat(sin_theta[:, None], wx.shape[0], axis=1)
        cos_theta2d = np.repeat(cos_theta[:, None], wx.shape[0], axis=1)
        dx = wx - gx2d[-1]
        dy = wy - gy2d[-1]
        new_wx = dx * cos_theta2d[-1] - dy * sin_theta2d[-1]
        new_wy = dx * sin_theta2d[-1] + dy * cos_theta2d[-1]
        walls = {}
        walls['x'] = new_wx
        walls['y'] = new_wy
    else:
        walls = tDict_sequence['walls']

    goal = tDict_sequence['goal']
    goal['x'] = np.zeros_like(gx)
    goal['y'] = np.zeros_like(gy)
    goal['a'] = np.zeros_like(ga)

    timestamp = tDict_sequence['timestamp']
    indices = tDict_sequence['indices']
    metrics_ft = tDict_sequence['metrics']
    context = tDict_sequence['context']

    tensor_dict = {'timestamp': timestamp,
                   'indices': indices,
                   'robot': robot,
                   'goal': goal,
                   'people': people,
                   'objects': objects,
                   'walls': walls,
                   'metrics': metrics_ft,
                   'context': context}

    return tensor_dict
