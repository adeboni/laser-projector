"""This module simulates the sierpinski pyramid"""

import threading
import socket
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
from laser_point import *

HUMAN_HEIGHT = 5
SIDE_LENGTH = 39
LASER_PROJECTION_ANGLE = 45 * np.pi / 180

triangle_height = np.sqrt(SIDE_LENGTH**2 - (SIDE_LENGTH/2)**2)
tetra_height = SIDE_LENGTH * np.sqrt(2/3)
projection_bottom = tetra_height / 4
projection_top = tetra_height / 2

vertices = [
    np.array([-SIDE_LENGTH/2, -triangle_height/3, 0]),
    np.array([SIDE_LENGTH/2, -triangle_height/3, 0]),
    np.array([0, triangle_height*2/3, 0]),
    np.array([0, 0, tetra_height]),
]

edges = [
    (vertices[0], vertices[1]),
    (vertices[0], vertices[2]),
    (vertices[1], vertices[2]),
    (vertices[1], vertices[3]),
    (vertices[0], vertices[3]),
    (vertices[2], vertices[3])
]

def find_edge_pos(edge, z):
    x = edge[0][0] + (z - edge[0][2]) * (edge[1][0] - edge[0][0]) / (edge[1][2] - edge[0][2])
    y = edge[0][1] + (z - edge[0][2]) * (edge[1][1] - edge[0][1]) / (edge[1][2] - edge[0][2])
    return (x, y, z)

surfaces = [
    np.array([find_edge_pos(edges[4], projection_bottom), find_edge_pos(edges[4], projection_top), 
              find_edge_pos(edges[5], projection_top), find_edge_pos(edges[5], projection_bottom)]),
    np.array([find_edge_pos(edges[3], projection_bottom), find_edge_pos(edges[3], projection_top), 
              find_edge_pos(edges[5], projection_top), find_edge_pos(edges[5], projection_bottom)]),
    np.array([find_edge_pos(edges[3], projection_bottom), find_edge_pos(edges[3], projection_top), 
              find_edge_pos(edges[4], projection_top), find_edge_pos(edges[4], projection_bottom)])
]

def find_surface_normal(surface):
    pn = np.cross(surface[1] - surface[0], surface[2] - surface[0])
    if pn[2] < 0:
        pn = -pn
    return pn / np.linalg.norm(pn)

plane_normals = np.array([find_surface_normal(surface) for surface in surfaces])
plane_points = np.array([surface[0] for surface in surfaces])
center_line = [(vertices[0] + vertices[2]) / 2, (0, 0, tetra_height)]
center_point = find_edge_pos(center_line, projection_bottom + (projection_top - projection_bottom) / 2)
target_vector = np.array([center_point[0], center_point[1], center_point[2] - HUMAN_HEIGHT])
target_vector = target_vector / np.linalg.norm(target_vector)
target_yaw = np.arctan2(target_vector[1], target_vector[0])
target_pitch = np.arctan2(-target_vector[2], np.sqrt(target_vector[0]**2 + target_vector[1]**2))
yaw_matrix = np.array([[np.cos(target_yaw), -np.sin(target_yaw), 0], [np.sin(target_yaw), np.cos(target_yaw), 0], [0, 0, 1]])
pitch_matrix = np.array([[np.cos(target_pitch), 0, np.sin(target_pitch)], [0, 1, 0], [-np.sin(target_pitch), 0, np.cos(target_pitch)]])

tp_orig = np.array([
    [0, 2048, 0],
    [2048, 4095, 0],
    [4095, 2048, 0],
    [2048, 0, 0],
])
transforms = []
inv_transforms = []

lasers = [
    np.array(find_edge_pos(edges[3], projection_bottom)),
    np.array(find_edge_pos(edges[4], projection_bottom)),
    np.array(find_edge_pos(edges[5], projection_bottom))
]
laser_centers = [laser - np.dot(laser - pp, pn) * pn 
                 for laser, pn, pp in zip(lasers, plane_normals, plane_points)]
laser_distance = np.linalg.norm(laser_centers[0] - lasers[0])
half_width = laser_distance * np.tan(LASER_PROJECTION_ANGLE)

for lc, pn in zip(laser_centers, plane_normals):
    v1 = np.array([-pn[1], pn[0], 0])
    v1 = v1 / np.linalg.norm(v1)
    v2 = np.cross(pn, v1) 
    tp_new = np.array([lc + half_width * (tpo[0] * v1 + tpo[1] * v2) for tpo in [(1, 0), (0, 1), (-1, 0), (0, -1)]])
    a = np.concatenate((tp_orig, np.ones((tp_orig.shape[0], 1))), axis=1)
    b = np.concatenate((tp_new, np.ones((tp_new.shape[0], 1))), axis=1)
    t, _, _, _ = np.linalg.lstsq(a, b, rcond=None)
    transforms.append(t.T)
    t, _, _, _ = np.linalg.lstsq(b, a, rcond=None)
    inv_transforms.append(t.T)

def sierpinski_to_laser_coords(laser_index, x, y, z):
    return np.dot(inv_transforms[laser_index], [x, y, z, 1])[:2]

def laser_to_sierpinksi_coords(laser_index, x, y):
    return np.dot(transforms[laser_index], [x, y, 0, 1])[:3]

def get_laser_coordinate_bounds():
    return [sierpinski_to_laser_coords(0, *p) for p in surfaces[0]]

def get_laser_min_max_interior():
    bounds = get_laser_coordinate_bounds()
    _xs = sorted([b[0] for b in bounds])
    min_x, max_x = _xs[1], _xs[2]
    min_y, max_y = min(b[1] for b in bounds), max(b[1] for b in bounds)
    return (min_x, max_x, min_y, max_y)

def point_in_triangle(a, b, c, p):
    def same_side(p1, p2, a, b):
        return np.dot(np.cross(b - a, p1 - a), np.cross(b - a, p2 - a)) >= 0
    return same_side(p, a, b, c) and same_side(p, b, a, c) and same_side(p, c, a, b)

def point_in_surface(s, p):
    return point_in_triangle(s[0], s[1], s[2], p) or point_in_triangle(s[2], s[3], s[0], p)

def apply_quaternion(quaternion):
    return np.dot(yaw_matrix, np.dot(pitch_matrix, quaternion.rotate([1, 0, 0])))

def get_wand_projection(quaternion):
    start = np.array([0, 0, HUMAN_HEIGHT])
    end = apply_quaternion(quaternion)
    end[2] += HUMAN_HEIGHT
    v = end - start
    if v[2] < 0:
        return None
    for i, (pn, pp, s) in enumerate(zip(plane_normals, plane_points, surfaces)):
        denom = np.dot(v, pn)
        if denom < 0.01:
            continue
        point = end + (np.dot(pp - end, pn / denom) * v)
        if point_in_surface(s, point):
            return (i, point)
    return None

laser_lines = [None] * 3
def _laser_thread(laser_index):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', 8090 + laser_index))
        curr_seq = 0
        while True:
            data, _ = sock.recvfrom(1024)
            raw_bytes = list(data)
            seq = raw_bytes.pop(0)
            if seq != (curr_seq + 1) % 255:
                curr_seq = seq
                continue
            curr_seq = seq

            segments = []
            for i in range(0, len(raw_bytes), 6):
                chunk = raw_bytes[i:i + 6]
                if len(chunk) != 6:
                    break
                new_point = LaserPoint.from_bytes(laser_index, chunk)
                segments.append([*laser_to_sierpinksi_coords(laser_index, new_point.x, new_point.y), 
                                 new_point.r, new_point.g, new_point.b])
            laser_lines[laser_index] = segments
    except:
        pass

if __name__ == '__main__':
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim((-25, 25))
    ax.set_ylim((-25, 25))
    ax.set_zlim((0, 40))
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.view_init(20, 50)

    for e1, e2 in edges:
        ax.plot([e1[0], e2[0]], [e1[1], e2[1]], [e1[2], e2[2]], color='k')
        
    for surface in surfaces:
        ax.plot_trisurf(*[[s[i] for s in surface] for i in range(3)], color='y', alpha=0.2)

    for laser, laser_center in zip(lasers, laser_centers):
        ax.plot([laser[0]], [laser[1]], [laser[2]], c='k', linestyle='', marker='o', alpha=0.2)
        ax.plot([laser[0], laser_center[0]], [laser[1], laser_center[1]], [laser[2], laser_center[2]], color='k', alpha=0.2)

    laser_plots = [ax.plot([], [], [], c=c, alpha=0.6) for c in ['r', 'g', 'b']]

    for i in range(3):
        threading.Thread(target=_laser_thread, args=(i,), daemon=True).start()

    def animate(_):
        for i in range(3):
            if laser_lines[i]:
                xs, ys, zs = [], [], []
                for ll in laser_lines[i]:
                    xs.append(ll[0])
                    ys.append(ll[1])
                    zs.append(ll[2])
                laser_plots[i][0].set_data(xs, ys)
                laser_plots[i][0].set_3d_properties(zs)

    ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
    plt.show()
