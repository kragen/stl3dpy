#!/usr/bin/python
"""Simple library for generating STL in pure Python.
"""
from __future__ import division

import math
import sys                      # for warn

def mesh(rows):
    "Turn a rectangular mesh into a sequence of triangles."
    for ii in range(1, len(rows)):
        last, this = rows[ii-1:ii+1]
        for jj in range(1, len(this)):
            aa, bb = last[jj-1:jj+1]
            cc, dd = this[jj-1:jj+1]

            yield (aa, bb, cc)
            yield (bb, dd, cc)
    

def extrude_mesh(rows, vec):
    rows = list(rows)
    basic_surface = list(mesh(rows))
    for triangle in basic_surface:
        yield triangle

    for triangle in flipped(vec, basic_surface):
        yield triangle

    # Now generate the four edges.
    # XXX it would be a lot easier to concatenate them!
    bottom_edge = [rows[0], [translate(vert, vec) for vert in rows[0]]]
    for triangle in mesh(bottom_edge):
        yield reverse_direction(triangle)

    top_edge = [rows[-1], [translate(vert, vec) for vert in rows[-1]]]
    for triangle in mesh(top_edge):
        yield triangle

    left_edge_line = [row[0] for row in rows]
    left_edge = [[vert, translate(vert, vec)] for vert in left_edge_line]
    for triangle in mesh(left_edge):
        yield reverse_direction(triangle)

    right_edge_line = [row[-1] for row in rows]
    right_edge = [[vert, translate(vert, vec)] for vert in right_edge_line]
    for triangle in mesh(right_edge):
        yield triangle

def flipped(vec, surface):
    "Generate a flipped version of surface translated by vec."
    for triangle in surface:
        yield reverse_direction(translate_verts(vec, triangle))

def translate_surface(vec, surface):
    for triangle in surface:
        yield translate_verts(vec, triangle)

def translate_verts(vec, verts):
    return [translate(vert, vec) for vert in verts]

def translate((x, y, z), (dx, dy, dz)):
    return (x+dx, y+dy, z+dz)

def reverse_direction((p1, p2, p3)):
    return p1, p3, p2

def stl_file(triangles, name):
    name = name.replace(' ', '_')
    yield "solid %s\n" % name
    for triangle in triangles:
        nn = normal(triangle)
        yield "  facet normal %f %f %f\n" % nn
        yield "    outer loop\n"
        for point in triangle:
            yield "      vertex %f %f %f\n" % point
        yield "    endloop\n"
        yield "  endfacet\n"
    yield "endsolid %s\n" % name

def normal((p1, p2, p3)):
    v1x, v1y, v1z = [p1x - p2x for p1x, p2x in zip(p1, p2)]
    v2x, v2y, v2z = [p1x - p3x for p1x, p3x in zip(p1, p3)]
    return normalize((v1z * v2y - v1y * v2z,
                      v1z * v2x - v1x * v2z,
                      v1y * v2x - v1x * v2y))

def normalize((x, y, z)):
    norm = (x**2 + y**2 + z**2)**0.5
    if norm == 0:
        warn("normalizing zero vector")
        return (x, y, z)
    return (x/norm, y/norm, z/norm)

def warn(astring):
    sys.stderr.write(astring + '\n')

class Polyline:
    def __init__(self, startpoint):
        self.points = [startpoint]

    def rlineto(self, vec):
        self.lineto(translate(self.points[-1], vec))
        return self

    def lineto(self, point):
        self.points.append(point)
        return self

    def verts(self):
        return self.points

def convex_fill(center, path):
    "Fill a convex polygon from a point in its center with triangles."
    for ii in range(len(path)):
        yield (center, path[ii], path[(ii+1) % len(path)])

def z_rotate_surface(angle, surface):
    for triangle in surface:
        yield z_rotate_vertices(angle, triangle)

def z_rotate_vertices(angle, verts):
    return [(x*math.cos(angle) - y*math.sin(angle),
             y*math.cos(angle) + x*math.sin(angle),
             z)
            for x, y, z in verts]
