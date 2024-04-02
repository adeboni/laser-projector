"""This module simulates the sierpinski pyramid"""

import threading
import socket
import numpy as np
import pyquaternion
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
    return pn / np.linalg.norm(pn)

plane_normals = np.array([find_surface_normal(surface) for surface in surfaces])
plane_points = np.array([surface[0] for surface in surfaces])

center_line = [(vertices[0] + vertices[2]) / 2, (0, 0, tetra_height)]
center_point = find_edge_pos(center_line, projection_bottom + (projection_top - projection_bottom) / 2)

tp_offsets = [
    [[1, 0], [0, 1], [-1, 0], [0, -1]],
    [[-1, 0], [0, 1], [1, 0], [0, -1]],
    [[1, 0], [0, 1], [-1, 0], [0, -1]]
]
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

for lc, pn, tpo in zip(laser_centers, plane_normals, tp_offsets):
    v1 = np.array([-pn[1], pn[0], 0])
    v1 = v1 / np.linalg.norm(v1)
    v2 = np.cross(pn, v1) 
    tp_new = np.array([lc + half_width * (tpo[0] * v1 + tpo[1] * v2) for tpo in tpo])
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

def point_in_triangle(a, b, c, p):
    same_side = lambda p1, p2, a, b: np.dot(np.cross(b - a, p1 - a), np.cross(b - a, p2 - a)) >= 0
    return same_side(p, a, b, c) and same_side(p, b, a, c) and same_side(p, c, a, b)

def point_in_surface(s, p):
    return point_in_triangle(s[0], s[1], s[2], p) or point_in_triangle(s[2], s[3], s[0], p)

def find_quat(start, end):
    cross = np.cross(start, end)
    axis = cross / np.linalg.norm(cross)
    theta = np.arctan(np.linalg.norm(cross) / np.dot(start, end))
    return pyquaternion.Quaternion(axis=axis, angle=theta)

def get_wand_projection(start, end):
    for i, (pn, pp, s) in enumerate(zip(plane_normals, plane_points, surfaces)):
        v = start - end
        point = end + (np.dot(pp - end, pn / np.dot(v, pn)) * v)
        if v[2] > 0 and point_in_surface(s, point):
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

def joystick_quaternion():
    import pygame
    pygame.init()
    controller = pygame.joystick.Joystick(0)
    wand_offset = pyquaternion.Quaternion(1, 0, 0, -1)
    q_init = pyquaternion.Quaternion(w=controller.get_axis(5), x=controller.get_axis(0), y=controller.get_axis(1), z=controller.get_axis(2))
    q_init = wand_offset.rotate(q_init)
    start = np.array([1, 0, 0])
    target_vector = np.array([center_point[0], center_point[1], center_point[2] - HUMAN_HEIGHT])
    q_target = find_quat(start, target_vector)
    q_div = q_target / q_init
    while True:
        pygame.event.pump()
        q = pyquaternion.Quaternion(w=controller.get_axis(5), x=controller.get_axis(0), y=controller.get_axis(1), z=controller.get_axis(2))
        #yield q_div * wand_offset.rotate(q)
        yield wand_offset.rotate(q)
        
def joystick_sim():
    q_init = pyquaternion.Quaternion(w=0.280, x=0.284, y=0.882, z=0.252)

    start = np.array([1, 0, 0])
    target_vector = np.array([center_point[0], center_point[1], center_point[2] - HUMAN_HEIGHT])
    q_target = find_quat(start, target_vector)
    
    v1 = q_target.rotate(start)
    x = np.array([-1.0 * v1[0] * v1[2], -1.0 * v1[1] * v1[2], v1[0]**2 + v1[1]**2]) / np.sqrt(v1[0]**2 + v1[1]**2) 
    
    print(v1, v2)
    
    while True:
        q = q_init
        yield (q_target / q_init) * q

def mouse_quaternion():
    import pyautogui
    screen_width, screen_height = pyautogui.size()
    start = np.array([1, 0, 0])
    target_vector = np.array([center_point[0], center_point[1], center_point[2] - HUMAN_HEIGHT])
    mouse_offset = find_quat(start, target_vector)
    while True:
        mouse = pyautogui.position()
        end = np.array([1, np.interp(mouse.x, [0, screen_width], [1, -1]), np.interp(mouse.y, [0, screen_height], [-1, 1])])
        yield mouse_offset * find_quat(start, end)

if __name__ == '__main__':
    quaternion_generator = joystick_sim()

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim((-25, 25))
    ax.set_ylim((-25, 25))
    ax.set_zlim((0, 40))
    ax.view_init(20, 50)

    for e1, e2 in edges:
        ax.plot([e1[0], e2[0]], [e1[1], e2[1]], [e1[2], e2[2]], color='k')

    for surface in surfaces:
        x = [s[0] for s in surface]
        y = [s[1] for s in surface]
        z = [s[2] for s in surface]
        ax.plot_trisurf(x, y, z, color='y', alpha=0.2)

    for laser, laser_center in zip(lasers, laser_centers):
        ax.plot([laser[0]], [laser[1]], [laser[2]], c='k', linestyle='', marker='o', alpha=0.2)
        ax.plot([laser[0], laser_center[0]], [laser[1], laser_center[1]], [laser[2], laser_center[2]], color='k', alpha=0.2)

    lines = sum([ax.plot([], [], [], c=c) for c in ['r', 'g', 'b']], [])
    projection = ax.plot([], [], [], c='r', linestyle='', marker='o')
    #ax.plot([center_point[0]], [center_point[1]], [center_point[2]], c='b', linestyle='', marker='o')
    laser_plots = [ax.plot([], [], [], c='r', alpha=0.6) for _ in range(3)]
    startpoints = np.array([[-2, 0, 0], [0, -2, 0], [0, 0, -2]])
    endpoints =  np.array([[2, 0, 0], [0, 2, 0], [0, 0, 2]])

    for i in range(3):
        threading.Thread(target=_laser_thread, args=(i,), daemon=True).start()

    def animate(_):
        q = next(quaternion_generator)

        for i in range(3):
            if laser_lines[i]:
                xs = []
                ys = []
                zs = []
                for ll in laser_lines[i]:
                    xs.append(ll[0])
                    ys.append(ll[1])
                    zs.append(ll[2])
                laser_plots[i][0].set_data(xs, ys)
                laser_plots[i][0].set_3d_properties(zs)

        for axis, (line, start, end) in enumerate(zip(lines, startpoints, endpoints)):
            start = q.rotate(start)
            end = q.rotate(end)
            start[2] += HUMAN_HEIGHT
            end[2] += HUMAN_HEIGHT
            line.set_data([start[0], end[0]], [start[1], end[1]])
            line.set_3d_properties([start[2], end[2]])
            if axis == 0:
                projection[0].set_data([], [])
                projection[0].set_3d_properties([])
                wand_projection = get_wand_projection(start, end)
                if wand_projection:
                    laser_index, wand_point = wand_projection
                    # wand_point is in 3D here, but we're transforming it to 2D laser coordinates and then back to 3D
                    laser_x, laser_y = sierpinski_to_laser_coords(laser_index, *wand_point)
                    wand_point = laser_to_sierpinksi_coords(laser_index, laser_x, laser_y)
                    projection[0].set_data([wand_point[0]], [wand_point[1]])
                    projection[0].set_3d_properties([wand_point[2]])

    ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
    plt.show()
