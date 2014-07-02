#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Generate a fucking shower curtain ring to 3-D print.

My plan is to make something basically planar, so it can bend and
twist, and then give it a sort of rounded T-shape at one end and a
T-shaped slot at the other.  My `extrude_mesh` function is not that
well suited for making things with holes in them, but `mesh` can be
bent to the task.

"""
from __future__ import division

from math import sin, cos, pi
import sys

import stl3d

def fragment_count(fn, theta):
    return int(round(theta*fn/2/pi))

def arc(r, start_theta, end_theta, fn):
    start_ii = fragment_count(fn, start_theta)
    end_ii = fragment_count(fn, end_theta)
    angles = [ii * 2 * pi / fn for ii in range(start_ii, end_ii+1)]
    return [(cos(theta) * r, sin(theta) * r, 0) for theta in angles]

def main(argv):
    rod_diameter = 25           # mm
    rr = rod_diameter / 2.0     # radius of rod
    strip_width = 6
    gap = 1                     # radian
    rr_adjusted = rr * 2*pi / (2*pi - gap) # inner circumference after closing

    ri = rr_adjusted + 2        # leave some slip space
    ro = ri + strip_width       # radius outer
    fn = 256            # number of different angles to use for the arc
    angles = [ii * 2 * pi / fn for ii in range(int(gap*fn/2/pi), fn+1)]
    thickness = 0.4             # mm; stiff but flexible
    disp = (0, 0, thickness)    # displacement vector between the sides
    t_width = 2                 # width of the T stem
    t_height = 2*t_width        # height of the T stem
    t_incut = (strip_width - t_width) / 2.0
    clearance = 0.25            # mm to leave between parts to slide smoothly
    t_top_width = strip_width

    spacing = 50                # mm between objects

    inner_edge = arc(ri, 0, 2*pi-gap, fn)
    outer_edge = arc(ro, 0, 2*pi-gap, fn)
    bottom = list(stl3d.mesh(zip(outer_edge, inner_edge)))
    inner_edge_top = stl3d.translate_verts(disp, inner_edge)
    outer_edge_top = stl3d.translate_verts(disp, outer_edge)
    top = list(stl3d.mesh(zip(inner_edge_top, outer_edge_top)))
    inner_surface = list(stl3d.mesh(zip(inner_edge, inner_edge_top)))
    outer_surface = list(stl3d.mesh(zip(outer_edge_top, outer_edge)))

    # The circles start off going y+ from the positive X-axis.
    t_start = (stl3d.Polyline(inner_edge[0])
               .rlineto((t_incut, 0, 0))
               .rlineto((0, -t_height, 0))
               .verts())
    t_start.reverse()

    t_end = (stl3d.Polyline(outer_edge[0])
             .rlineto((-t_incut, 0, 0))
             .rlineto((0, -t_height, 0))
             .verts())

    t_center = ((ri + ro)/2.0, -t_height, 0)
    t_cap_line = stl3d.translate_verts(t_center, 
                                       arc(t_top_width/2.0, pi, 2*pi, fn))
    t_cap_line.reverse()
    t_path = t_end + t_cap_line + t_start
    t_path_top = stl3d.translate_verts(disp, t_path)
    t_surface = list(stl3d.mesh(zip(t_path, t_path_top)))
    t_fill_center = stl3d.translate(t_center, (0, -t_top_width/4.0, 0))
    t_fill = list(stl3d.convex_fill(t_fill_center, t_path[1:-1]))
    t_fill_top = list(stl3d.flipped(disp, t_fill))
    tt = t_surface + t_fill + t_fill_top

    # We’ll construct the slot in a convenient place, then rotate it
    # into place.
    slot_width = t_width + 2*clearance
    slot_length = t_top_width + 2*clearance
    slot_cap_center = ((ri+ro)/2.0, slot_length, 0)
    slot_outer_arc = stl3d.translate_verts(slot_cap_center,
                                           arc(strip_width/2.0, 0, pi, fn))
    slot_outer_arc.reverse()
    slot_arc_fill = list(stl3d.convex_fill(slot_cap_center, slot_outer_arc))
    slot_arc_fill_top = list(stl3d.flipped(disp, slot_arc_fill))
    slot_outer_path = ([inner_edge[0]] + slot_outer_arc + [outer_edge[0]])
    slot_outer_path_top = stl3d.translate_verts(disp, slot_outer_path)
    slot_outer_surface = list(stl3d.mesh(zip(slot_outer_path, 
                                             slot_outer_path_top)))
    slot_side_width = (strip_width - slot_width) / 2.0
    slot_inside_edge = (stl3d.Polyline(inner_edge[0])
                        .rlineto((slot_side_width, 0, 0))
                        .rlineto(disp)
                        .rlineto((-slot_side_width, 0, 0))
                        .verts())
    slot_inside_edge_2 = stl3d.translate_verts((0, slot_length, 0),
                                               slot_inside_edge)
    slot_inside_surface = list(stl3d.mesh(zip(slot_inside_edge,
                                              slot_inside_edge_2)))

    slot_outside_edge = (stl3d.Polyline(outer_edge[0])
                         .rlineto((-slot_side_width, 0, 0))
                         .rlineto(disp)
                         .rlineto((slot_side_width, 0, 0))
                         .verts())
    slot_outside_edge.reverse()
    slot_outside_edge_2 = stl3d.translate_verts((0, slot_length, 0),
                                                slot_outside_edge)
    slot_outside_surface = list(stl3d.mesh(zip(slot_outside_edge,
                                               slot_outside_edge_2)))
    slot_end_line = [slot_outside_edge_2[2], slot_inside_edge_2[1]]
    slot_end_line_2 = stl3d.translate_verts(disp, slot_end_line)
    slot_end_surface = list(stl3d.mesh(zip(slot_end_line, slot_end_line_2)))
    slot_start_surface = list(stl3d.flipped((0, -slot_length, 0),
                                            slot_end_surface))

    slot_unrotated = (slot_arc_fill
                      + slot_arc_fill_top
                      + slot_outer_surface
                      + slot_inside_surface
                      + slot_outside_surface
                      + slot_end_surface
                      + slot_start_surface
                      )
    slot_rotate_fragment_count = fragment_count(fn, -gap)
    slot_rotate_angle = 2*pi*slot_rotate_fragment_count / fn
    slot = list(stl3d.z_rotate_surface(slot_rotate_angle, slot_unrotated))

    shower_ring = bottom + top + inner_surface + outer_surface + tt + slot
    shower_rings = shower_ring

    for line in stl3d.stl_file(shower_rings, name="shower rings"):
        sys.stdout.write(line)

if __name__ == '__main__':
    main(sys.argv)
