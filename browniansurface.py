#!/usr/bin/python
"""Generate a 3-D STL file of a surface using Brownian noise.

The purpose here was to generate an STL file of an interesting object
as quickly and dirtily as possible, because I had to go meet a friend
after printing it, so I wrote the original version of this program in
42 minutes (and then spent another 10 minutes figuring out that I
wanted to turn the object upside down).  Some of the surface normals
were wrong, but slic3r managed to slice it anyway, so I got it printed.

The surface here is in some sense a heightfield, but to ensure 
printability, we print it vertically.

"""
from __future__ import division
import random
import sys

import stl3d

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

if __name__ == '__main__':
    seed = 0 if len(sys.argv) < 2 else int(sys.argv[1])
    pp = list(points(seed=seed, max_x=40, dx=3, dy=.5, max_z=20, dz=2.5))
    pp.reverse()
    for line in stl3d.stl_file(stl3d.extrude_mesh(pp, (0, .75, 0)),
                               name="brownian surface seed %s" % seed):
        sys.stdout.write(line)
