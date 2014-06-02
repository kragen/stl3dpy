#!/usr/bin/python
"""Generate a 3-D STL file of a surface using Brownian noise.

The purpose here was to generate an STL file of an interesting object
as quickly and dirtily as possible, because I had to go meet a friend
after printing it, so I wrote the original version of this program in
42 minutes (and then spent another 10 minutes figuring out that I
wanted to turn the object upside down).  Some of the surface normals
are wrong, but slic3r managed to slice it anyway, so I got it printed.

The surface here is in some sense a heightfield, but to ensure 
printability, we print it vertically.

"""
from __future__ import division
import random
import sys

def points(seed, max_x, dx, dy, max_z, dz):
    "Generate the rows of the heightfield, a sequence of lists of 3-tuples."
    generator = random.Random()
    generator.seed(seed)

    nx = int(max_x // dx)
    y = [0] * nx
    zi = int(max_z // dz)
    def row():
        return [(xi * dx, yi, zi * dz) for xi, yi in enumerate(y)]

    while zi > 0:
        yield row()
        y = [yi + (generator.random() * 2 - 1) * dy for yi in y]
        # smooth to keep things manageable?
        zi -= 1
    
    yield row()

def mesh(rows):
    "Turn a rectangular mesh into a sequence of triangles."
    for ii in range(1, len(rows)):
        last, this = rows[ii-1:ii+1]
        for jj in range(1, len(this)):
            aa, bb = last[jj-1:jj+1]
            cc, dd = this[jj-1:jj+1]

            yield (aa, bb, cc)
            yield (bb, dd, cc)
    

def triangles(rows, thickness):
    rows = list(rows)
    # Generate in parallel the positive-y and negative-y surfaces:
    for triangle in mesh(rows):
        yield triangle
        yield reverse_direction(offset_triangle_by((0, thickness, 0), triangle))

    # Now generate the four edges.
    bottom_edge = [rows[0], [(x, y+thickness, z) for x, y, z in rows[0]]]
    for triangle in mesh(bottom_edge):
        yield reverse_direction(triangle)

    top_edge = [rows[-1], [(x, y+thickness, z) for x, y, z in rows[-1]]]
    for triangle in mesh(top_edge):
        yield triangle

    left_edge_line = [row[0] for row in rows]
    left_edge = [[(x, y, z), (x, y+thickness, z)] for x, y, z in left_edge_line]
    for triangle in mesh(left_edge):
        yield reverse_direction(triangle)

    right_edge_line = [row[-1] for row in rows]
    right_edge = [[(x, y, z), (x, y+thickness, z)] for x, y, z in right_edge_line]
    for triangle in mesh(right_edge):
        yield triangle

def offset_triangle_by((dx, dy, dz), triangle):
    return tuple((x+dx, y+dy, z+dz) for x, y, z in triangle)

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
    return (x/norm, y/norm, z/norm)

if __name__ == '__main__':
    seed=0
    pp = list(points(seed=seed, max_x=40, dx=5, dy=2, max_z=20, dz=5))
    pp.reverse()
    # for row in pp:
    #     print row
    # for tri in triangles(pp, thickness=1):
    #     print tri
    for line in stl_file(triangles(pp, thickness=1), name="brownian surface seed %s" % seed):
        sys.stdout.write(line)
