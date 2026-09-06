#!/usr/bin/env python3
"""
Generate a luxury Swiss-grade Mechanical Automatic Chronograph with animated ticking hands.
Features:
- 316L Stainless Steel Case with sculpted ergonomic curved lugs, integrated bracelet end-links,
  knurled winding crown, crown guards, and dual chronograph pump pushers.
- Ceramic Tachymeter Bezel with engraved calibrations (500 to 60 units/hr).
- Applied Rhodium Hour Batons, 60-second chapter track, and 3 sub-dial tracks (distinct high-contrast system).
- Obsidian Sunburst Dial with 3 recessed Tri-Compax sub-dials.
- Separate Faceted Dauphine Hour & Minute Hands, Central Red Chrono Sweeper, and Small Seconds Hand.
- High-beat 28,800 vph (4 Hz) club-tooth escapement wheel & synthetic ruby pallet fork.
- Glucydur balance wheel with Nivarox hairspring.
- 4-wheel gear train & micro-machined 6-pillar column wheel chronograph clutch.
- Perlage mainplate & heavy tungsten oscillating rotor.
- Dual synthetic sapphire crystals (front domed, rear flat exhibition).
"""

import json
import math
import struct
import zlib
from pathlib import Path

CENTER_Y = 0.85

def pack_normal(x, y, z):
    l = math.hypot(x, y, z)
    if l > 1e-9:
        x, y, z = x / l, y / l, z / l
    else:
        x, y, z = 0.0, 0.0, 1.0
    def to_i16(v):
        clamped = max(-1.0, min(1.0, v))
        return int(clamped * 32767)
    return [to_i16(x), to_i16(y), to_i16(z)]

class ChronoBuilder:
    def __init__(self):
        self.parts = []
        self.blob = bytearray()
        self.total_triangles = 0

    def append_part(self, part_id, name, concept_id, system, verts, norms, idxs, explode_offset=None):
        v_count = len(verts) // 3
        i_count = len(idxs)
        tri_count = i_count // 3
        self.total_triangles += tri_count

        while len(self.blob) % 4 != 0:
            self.blob.append(0)
        pos_offset = len(self.blob)
        self.blob.extend(struct.pack(f'<{len(verts)}f', *verts))

        while len(self.blob) % 2 != 0:
            self.blob.append(0)
        norm_offset = len(self.blob)
        self.blob.extend(struct.pack(f'<{len(norms)}h', *norms))

        while len(self.blob) % 4 != 0:
            self.blob.append(0)
        idx_offset = len(self.blob)
        self.blob.extend(struct.pack(f'<{len(idxs)}I', *idxs))

        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        for i in range(v_count):
            x, y, z = verts[i * 3], verts[i * 3 + 1], verts[i * 3 + 2]
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            min_z, max_z = min(min_z, z), max(max_z, z)

        part_def = {
            'id': part_id,
            'name': name,
            'conceptId': concept_id,
            'system': system,
            'chunk': 0,
            'positions': pos_offset,
            'normals': norm_offset,
            'indices': idx_offset,
            'vertexCount': v_count,
            'indexCount': i_count,
            'bounds': [
                [round(min_x, 5), round(min_y, 5), round(min_z, 5)],
                [round(max_x, 5), round(max_y, 5), round(max_z, 5)]
            ]
        }
        if explode_offset:
            part_def['explodeOffset'] = [round(v, 4) for v in explode_offset]

        self.parts.append(part_def)
        print(f"  + {part_id:28} | {name:38} | {system:18} | {tri_count:5} tris | bounds: [{min_x:.3f},{min_y:.3f},{min_z:.3f}] -> [{max_x:.3f},{max_y:.3f},{max_z:.3f}]")

def make_cylinder(r_top, r_bot, height, z_center=0.0, segs=36, cx=0.0, cy=CENTER_Y):
    verts, norms, idxs = [], [], []
    half_h = height / 2.0
    z_top = z_center + half_h
    z_bot = z_center - half_h

    side_base = len(verts) // 3
    dr = r_bot - r_top
    slope_l = math.hypot(height, dr)
    nz = dr / slope_l if slope_l > 1e-9 else 0.0
    nr = height / slope_l if slope_l > 1e-9 else 1.0

    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_top * ca, cy + r_top * sa, z_top])
        norms.extend(pack_normal(ca * nr, sa * nr, nz))
        verts.extend([cx + r_bot * ca, cy + r_bot * sa, z_bot])
        norms.extend(pack_normal(ca * nr, sa * nr, nz))

    for i in range(segs):
        i0 = side_base + i * 2
        idxs.extend([i0, i0 + 2, i0 + 1, i0 + 2, i0 + 3, i0 + 1])

    top_base = len(verts) // 3
    verts.extend([cx, cy, z_top])
    norms.extend(pack_normal(0, 0, 1))
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        verts.extend([cx + r_top * math.cos(angle), cy + r_top * math.sin(angle), z_top])
        norms.extend(pack_normal(0, 0, 1))
    for i in range(segs):
        idxs.extend([top_base, top_base + i + 1, top_base + i + 2])

    bot_base = len(verts) // 3
    verts.extend([cx, cy, z_bot])
    norms.extend(pack_normal(0, 0, -1))
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        verts.extend([cx + r_bot * math.cos(angle), cy + r_bot * math.sin(angle), z_bot])
        norms.extend(pack_normal(0, 0, -1))
    for i in range(segs):
        idxs.extend([bot_base, bot_base + i + 2, bot_base + i + 1])

    return verts, norms, idxs

def make_ring(r_inner, r_outer, height, z_center=0.0, segs=36, cx=0.0, cy=CENTER_Y):
    verts, norms, idxs = [], [], []
    half_h = height / 2.0
    top_z = z_center + half_h
    bot_z = z_center - half_h

    v_base = len(verts) // 3
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_outer * ca, cy + r_outer * sa, top_z])
        norms.extend(pack_normal(ca, sa, 0))
        verts.extend([cx + r_outer * ca, cy + r_outer * sa, bot_z])
        norms.extend(pack_normal(ca, sa, 0))
    for i in range(segs):
        i0 = v_base + i * 2
        idxs.extend([i0, i0 + 2, i0 + 1, i0 + 2, i0 + 3, i0 + 1])

    v_base = len(verts) // 3
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_inner * ca, cy + r_inner * sa, top_z])
        norms.extend(pack_normal(-ca, -sa, 0))
        verts.extend([cx + r_inner * ca, cy + r_inner * sa, bot_z])
        norms.extend(pack_normal(-ca, -sa, 0))
    for i in range(segs):
        i0 = v_base + i * 2
        idxs.extend([i0, i0 + 1, i0 + 2, i0 + 2, i0 + 1, i0 + 3])

    v_base = len(verts) // 3
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_outer * ca, cy + r_outer * sa, top_z])
        norms.extend(pack_normal(0, 0, 1))
        verts.extend([cx + r_inner * ca, cy + r_inner * sa, top_z])
        norms.extend(pack_normal(0, 0, 1))
    for i in range(segs):
        i0 = v_base + i * 2
        idxs.extend([i0, i0 + 2, i0 + 1, i0 + 2, i0 + 3, i0 + 1])

    v_base = len(verts) // 3
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_outer * ca, cy + r_outer * sa, bot_z])
        norms.extend(pack_normal(0, 0, -1))
        verts.extend([cx + r_inner * ca, cy + r_inner * sa, bot_z])
        norms.extend(pack_normal(0, 0, -1))
    for i in range(segs):
        i0 = v_base + i * 2
        idxs.extend([i0, i0 + 1, i0 + 2, i0 + 2, i0 + 1, i0 + 3])

    return verts, norms, idxs

def make_oriented_box(w, h, d, cx=0.0, cy=CENTER_Y, cz=0.0, angle=0.0):
    hw, hh, hd = w / 2.0, h / 2.0, d / 2.0
    ca, sa = math.cos(angle), math.sin(angle)

    def rot(lx, ly):
        return cx + lx * ca - ly * sa, cy + lx * sa + ly * ca

    def rot_n(nx, ny, nz):
        return pack_normal(nx * ca - ny * sa, nx * sa + ny * ca, nz)

    face_defs = [
        ([-hw, -hh, hd], [hw, -hh, hd], [hw, hh, hd], [-hw, hh, hd], (0, 0, 1)),
        ([hw, -hh, -hd], [-hw, -hh, -hd], [-hw, hh, -hd], [hw, hh, -hd], (0, 0, -1)),
        ([-hw, hh, hd], [hw, hh, hd], [hw, hh, -hd], [-hw, hh, -hd], (0, 1, 0)),
        ([-hw, -hh, -hd], [hw, -hh, -hd], [hw, -hh, hd], [-hw, -hh, hd], (0, -1, 0)),
        ([hw, -hh, hd], [hw, -hh, -hd], [hw, -hh, -hd], [hw, -hh, hd], (1, 0, 0)),
        ([-hw, -hh, -hd], [-hw, -hh, hd], [-hw, hh, hd], [-hw, hh, -hd], (-1, 0, 0)),
    ]

    verts, norms, idxs = [], [], []
    for c0, c1, c2, c3, norm in face_defs:
        base = len(verts) // 3
        pn = rot_n(*norm)
        for lx, ly, lz in [c0, c1, c2, c3]:
            gx, gy = rot(lx, ly)
            verts.extend([gx, gy, cz + lz])
            norms.extend(pn)
        idxs.extend([base, base + 1, base + 2, base, base + 2, base + 3])

    return verts, norms, idxs

# 1. Sapphire Crystal
def create_sapphire_crystal(radius=0.190, dome=0.013, thickness=0.005, z_base=0.055):
    verts, norms, idxs = [], [], []
    segs, rings = 40, 8
    for r in range(rings + 1):
        v = r / rings
        curr_r = v * radius
        curv = (1.0 - (v**2)) * dome
        for s in range(segs + 1):
            theta = (s / segs) * math.pi * 2
            ct, st = math.cos(theta), math.sin(theta)
            px = curr_r * ct
            py = CENTER_Y + curr_r * st
            pz = z_base + curv
            verts.extend([px, py, pz])
            nx = ct * (v * 0.35)
            ny = st * (v * 0.35)
            nz = 1.0 - (v * 0.15)
            norms.extend(pack_normal(nx, ny, nz))

    for r in range(rings):
        for s in range(segs):
            stride = segs + 1
            i0 = r * stride + s
            i1 = (r + 1) * stride + s
            i2 = (r + 1) * stride + (s + 1)
            i3 = r * stride + (s + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    inner_base = len(verts) // 3
    for r in range(rings + 1):
        v = r / rings
        curr_r = v * (radius - 0.004)
        curv = (1.0 - (v**2)) * (dome * 0.92)
        for s in range(segs + 1):
            theta = (s / segs) * math.pi * 2
            ct, st = math.cos(theta), math.sin(theta)
            px = curr_r * ct
            py = CENTER_Y + curr_r * st
            pz = (z_base - thickness) + curv
            verts.extend([px, py, pz])
            nx = -ct * (v * 0.35)
            ny = -st * (v * 0.35)
            nz = -1.0 + (v * 0.15)
            norms.extend(pack_normal(nx, ny, nz))

    for r in range(rings):
        for s in range(segs):
            stride = segs + 1
            i0 = inner_base + r * stride + s
            i1 = inner_base + (r + 1) * stride + s
            i2 = inner_base + (r + 1) * stride + (s + 1)
            i3 = inner_base + r * stride + (s + 1)
            idxs.extend([i0, i2, i1, i0, i3, i2])

    rim_base = len(verts) // 3
    for s in range(segs + 1):
        theta = (s / segs) * math.pi * 2
        ct, st = math.cos(theta), math.sin(theta)
        verts.extend([radius * ct, CENTER_Y + radius * st, z_base])
        norms.extend(pack_normal(ct, st, 0))
        verts.extend([(radius - 0.004) * ct, CENTER_Y + (radius - 0.004) * st, z_base - thickness])
        norms.extend(pack_normal(ct, st, 0))
    for s in range(segs):
        i0 = rim_base + s * 2
        idxs.extend([i0, i0 + 1, i0 + 2, i0 + 2, i0 + 1, i0 + 3])

    return verts, norms, idxs

# 2. Ceramic Tachymeter Bezel
def create_tachymeter_bezel(z_center=0.046):
    verts, norms, idxs = [], [], []
    ov, on, oi = make_ring(r_inner=0.216, r_outer=0.228, height=0.016, z_center=z_center, segs=54)
    verts.extend(ov); norms.extend(on); idxs.extend(oi)

    cv, cn, ci = make_ring(r_inner=0.188, r_outer=0.216, height=0.014, z_center=z_center + 0.001, segs=54)
    base = len(verts) // 3
    verts.extend(cv); norms.extend(cn); idxs.extend([idx + base for idx in ci])

    return verts, norms, idxs

# 3. High-Contrast Rhodium Indices & Tachymeter Calibrations
def create_dial_indices(radius=0.186, z_center=0.030):
    verts, norms, idxs = [], [], []

    # Bezel Tachymeter 12 o'clock triangle
    t_v, t_n, t_i = make_oriented_box(0.008, 0.012, 0.003, cx=0.0, cy=CENTER_Y + 0.203, cz=0.054, angle=0.0)
    verts.extend(t_v); norms.extend(t_n); idxs.extend(t_i)

    # 36 radial calibration marks on ceramic bezel
    for i in range(36):
        deg = 90 - (i * 10)
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        r_mid = 0.202
        bx = r_mid * ca
        by = CENTER_Y + r_mid * sa
        is_major = (i % 3 == 0)
        bw = 0.0035 if is_major else 0.002
        bl = 0.013 if is_major else 0.008
        tick_angle = rad - math.pi / 2.0
        tk_v, tk_n, tk_i = make_oriented_box(bw, bl, 0.003, cx=bx, cy=by, cz=0.054, angle=tick_angle)
        base = len(verts) // 3
        verts.extend(tk_v); norms.extend(tk_n); idxs.extend([idx + base for idx in tk_i])

    # 60-Second Outer Track Ticks on dial
    for sec in range(60):
        deg = 90 - (sec * 6)
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        is_5min = (sec % 5 == 0)
        r_pos = radius - 0.007
        tx = r_pos * ca
        ty = CENTER_Y + r_pos * sa
        w = 0.0035 if is_5min else 0.0018
        l = 0.010 if is_5min else 0.0055
        tick_angle = rad - math.pi / 2.0
        tk_v, tk_n, tk_i = make_oriented_box(w, l, 0.0025, cx=tx, cy=ty, cz=z_center + 0.002, angle=tick_angle)
        base = len(verts) // 3
        verts.extend(tk_v); norms.extend(tk_n); idxs.extend([idx + base for idx in tk_i])

    # 12 Applied 3D Faceted Rhodium Hour Batons
    for h in range(12):
        deg = 90 - (h * 30)
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        baton_r = radius * 0.74
        bx = baton_r * ca
        by = CENTER_Y + baton_r * sa
        baton_angle = rad - math.pi / 2.0

        if h == 0:
            for split in [-0.007, 0.007]:
                b_v, b_n, b_i = make_oriented_box(0.0055, 0.026, 0.005, cx=split, cy=by, cz=z_center + 0.004, angle=0.0)
                base = len(verts) // 3
                verts.extend(b_v); norms.extend(b_n); idxs.extend([idx + base for idx in b_i])
        else:
            is_cardinal = (h in [3, 6, 9])
            blen = 0.014 if is_cardinal else 0.024
            bwid = 0.0065 if is_cardinal else 0.0055
            b_v, b_n, b_i = make_oriented_box(bwid, blen, 0.005, cx=bx, cy=by, cz=z_center + 0.004, angle=baton_angle)
            base = len(verts) // 3
            verts.extend(b_v); norms.extend(b_n); idxs.extend([idx + base for idx in b_i])

    # 3 Sub-dial Chapter Rings and Calibration Ticks
    sub_coords = [(0.076, CENTER_Y), (0.0, CENTER_Y - 0.072), (-0.076, CENTER_Y)]
    for sx, sy in sub_coords:
        sv, sn, si = make_ring(0.038, 0.041, 0.002, z_center=z_center + 0.002, segs=32, cx=sx, cy=sy)
        base = len(verts) // 3
        verts.extend(sv); norms.extend(sn); idxs.extend([idx + base for idx in si])
        for t_idx in range(4):
            t_angle = t_idx * (math.pi / 2.0)
            tx = sx + 0.032 * math.cos(t_angle)
            ty = sy + 0.032 * math.sin(t_angle)
            tk_v, tk_n, tk_i = make_oriented_box(0.002, 0.006, 0.002, cx=tx, cy=ty, cz=z_center + 0.0025, angle=t_angle)
            base = len(verts) // 3
            verts.extend(tk_v); norms.extend(tk_n); idxs.extend([idx + base for idx in tk_i])

    return verts, norms, idxs

# 4. Sunburst Obsidian Dial Plate with 3 Recessed Sub-Dials
def create_dial_face(radius=0.186, z_center=0.030):
    verts, norms, idxs = [], [], []
    segs = 64
    center_idx = len(verts) // 3
    verts.extend([0.0, CENTER_Y, z_center])
    norms.extend(pack_normal(0, 0, 1))
    for s in range(segs + 1):
        theta = (s / segs) * math.pi * 2
        ct, st = math.cos(theta), math.sin(theta)
        verts.extend([radius * ct, CENTER_Y + radius * st, z_center])
        norms.extend(pack_normal(0, 0, 1))
    for s in range(segs):
        idxs.extend([center_idx, center_idx + s + 1, center_idx + s + 2])

    sub_configs = [
        (0.076, CENTER_Y, 0.038),
        (0.0, CENTER_Y - 0.072, 0.038),
        (-0.076, CENTER_Y, 0.038)
    ]
    for scx, scy, srad in sub_configs:
        pv, pn, pi = make_cylinder(srad, srad, 0.0025, z_center=z_center - 0.0012, segs=32, cx=scx, cy=scy)
        base = len(verts) // 3
        verts.extend(pv); norms.extend(pn); idxs.extend([idx + base for idx in pi])

    return verts, norms, idxs

# 5. Faceted Dauphine Hour Hand (Authored pointing straight UP at 12 o'clock)
def create_hour_hand(z_base=0.038):
    verts, norms, idxs = [], [], []
    h_len = 0.088
    h_w = 0.012
    # Hand points along +Y from (0.0, CENTER_Y)
    hw2 = h_w / 2.0
    tip_y = CENTER_Y + h_len
    ridge_y = CENTER_Y + h_len * 0.65

    base = len(verts) // 3
    verts.extend([
        0.0, CENTER_Y, z_base,
        -hw2, CENTER_Y + 0.012, z_base - 0.001,
        hw2, CENTER_Y + 0.012, z_base - 0.001,
        0.0, tip_y, z_base - 0.001,
        0.0, ridge_y, z_base + 0.0025  # Center ridge
    ])
    norms.extend(pack_normal(0, 0, 1) * 5)
    idxs.extend([
        base, base + 1, base + 4,
        base, base + 4, base + 2,
        base + 1, base + 3, base + 4,
        base + 2, base + 4, base + 3
    ])
    return verts, norms, idxs

# 6. Faceted Dauphine Minute Hand (Authored pointing straight UP at 12 o'clock)
def create_minute_hand(z_base=0.042):
    verts, norms, idxs = [], [], []
    m_len = 0.134
    m_w = 0.010
    mw2 = m_w / 2.0
    tip_y = CENTER_Y + m_len
    ridge_y = CENTER_Y + m_len * 0.70

    base = len(verts) // 3
    verts.extend([
        0.0, CENTER_Y, z_base,
        -mw2, CENTER_Y + 0.015, z_base - 0.001,
        mw2, CENTER_Y + 0.015, z_base - 0.001,
        0.0, tip_y, z_base - 0.001,
        0.0, ridge_y, z_base + 0.0025  # Center ridge
    ])
    norms.extend(pack_normal(0, 0, 1) * 5)
    idxs.extend([
        base, base + 1, base + 4,
        base, base + 4, base + 2,
        base + 1, base + 3, base + 4,
        base + 2, base + 4, base + 3
    ])
    return verts, norms, idxs

# 7. Central Chronograph Sweep Seconds Hand (Vibrant Racing Red, pointing straight UP at 12 o'clock)
def create_chrono_sweeper(z_pos=0.046):
    verts, norms, idxs = [], [], []
    needle_len = 0.158
    needle_w = 0.0022
    # Needle along +Y
    nv, nn, ni = make_oriented_box(needle_w, needle_len, 0.002, cx=0.0, cy=CENTER_Y + (needle_len / 2.0), cz=z_pos, angle=0.0)
    verts.extend(nv); norms.extend(nn); idxs.extend(ni)

    # Arrow tip
    tip_y = CENTER_Y + needle_len
    tv, tn, ti = make_oriented_box(0.007, 0.010, 0.002, cx=0.0, cy=tip_y, cz=z_pos, angle=0.0)
    base = len(verts) // 3
    verts.extend(tv); norms.extend(tn); idxs.extend([idx + base for idx in ti])

    # Circular counterweight at rear (down along -Y)
    cv, cn, ci = make_cylinder(0.0075, 0.0075, 0.0025, z_center=z_pos, segs=20, cx=0.0, cy=CENTER_Y - 0.024)
    base = len(verts) // 3
    verts.extend(cv); norms.extend(cn); idxs.extend([idx + base for idx in ci])

    # Rear stem connecting counterweight
    rv, rn, ri = make_oriented_box(needle_w, 0.024, 0.002, cx=0.0, cy=CENTER_Y - 0.012, cz=z_pos, angle=0.0)
    base = len(verts) // 3
    verts.extend(rv); norms.extend(rn); idxs.extend([idx + base for idx in ri])

    # Central pivot collar
    pv, pn, pi = make_cylinder(0.0055, 0.0055, 0.0035, z_center=z_pos + 0.001, segs=16, cx=0.0, cy=CENTER_Y)
    base = len(verts) // 3
    verts.extend(pv); norms.extend(pn); idxs.extend([idx + base for idx in pi])

    return verts, norms, idxs

# 8. Small Running Seconds Hand at 9 o'clock (Pivot: (-0.076, CENTER_Y))
def create_sub_seconds(z_base=0.038):
    verts, norms, idxs = [], [], []
    sx, sy = -0.076, CENTER_Y
    s_l = 0.026
    # Points straight up along +Y from (sx, sy)
    sh_v, sh_n, sh_i = make_oriented_box(0.0024, s_l, 0.002, cx=sx, cy=sy + (s_l / 2.0), cz=z_base, angle=0.0)
    verts.extend(sh_v); norms.extend(sh_n); idxs.extend(sh_i)
    # Center collar
    sp_v, sp_n, sp_i = make_cylinder(0.004, 0.004, 0.003, z_center=z_base + 0.001, segs=16, cx=sx, cy=sy)
    base = len(verts) // 3
    verts.extend(sp_v); norms.extend(sp_n); idxs.extend([idx + base for idx in sp_i])
    return verts, norms, idxs

# 9. Static Sub-Dial Needles (30-min at 3 o'clock, 12-hr at 6 o'clock, center pinion collar)
def create_sub_hands_static(z_base=0.038):
    verts, norms, idxs = [], [], []
    static_hands = [
        (0.076, CENTER_Y, math.radians(110), 0.024),
        (0.0, CENTER_Y - 0.072, math.radians(210), 0.024)
    ]
    for sx, sy, s_ang, s_l in static_hands:
        sh_v, sh_n, sh_i = make_oriented_box(0.0022, s_l, 0.002, cx=sx + (s_l/2)*math.cos(s_ang), cy=sy + (s_l/2)*math.sin(s_ang), cz=z_base, angle=s_ang - math.pi/2)
        base = len(verts) // 3
        verts.extend(sh_v); norms.extend(sh_n); idxs.extend([idx + base for idx in sh_i])
        sp_v, sp_n, sp_i = make_cylinder(0.0035, 0.0035, 0.003, z_center=z_base + 0.001, segs=16, cx=sx, cy=sy)
        base = len(verts) // 3
        verts.extend(sp_v); norms.extend(sp_n); idxs.extend([idx + base for idx in sp_i])

    # Central pinion cap ring
    cv, cn, ci = make_cylinder(0.008, 0.008, 0.007, z_center=z_base + 0.006, segs=24, cx=0.0, cy=CENTER_Y)
    base = len(verts) // 3
    verts.extend(cv); norms.extend(cn); idxs.extend([idx + base for idx in ci])

    return verts, norms, idxs

# 10. Escapement Wheel
def create_escapement_wheel(radius=0.062, z_center=0.012):
    verts, norms, idxs = [], [], []
    teeth = 15
    for t in range(teeth):
        angle = (t / teeth) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        tx, ty = radius * ca, CENTER_Y + radius * sa
        tv, tn, ti = make_oriented_box(0.005, 0.016, 0.004, cx=tx, cy=ty, cz=z_center, angle=angle + 0.35)
        base = len(verts) // 3
        verts.extend(tv); norms.extend(tn); idxs.extend([idx + base for idx in ti])

    wv, wn, wi = make_ring(r_inner=0.018, r_outer=radius, height=0.003, z_center=z_center, segs=36)
    base = len(verts) // 3
    verts.extend(wv); norms.extend(wn); idxs.extend([idx + base for idx in wi])

    hv, hn, hi = make_cylinder(0.012, 0.012, 0.008, z_center=z_center, segs=16)
    base = len(verts) // 3
    verts.extend(hv); norms.extend(hn); idxs.extend([idx + base for idx in hi])

    return verts, norms, idxs

# 11. Synthetic Ruby Pallet Lever
def create_pallet_fork(length=0.072, z_center=0.012):
    verts, norms, idxs = [], [], []
    bv, bn, bi = make_oriented_box(0.008, length, 0.004, cx=0.035, cy=CENTER_Y + 0.035, cz=z_center, angle=0.45)
    verts.extend(bv); norms.extend(bn); idxs.extend(bi)

    for px, py in [(0.018, 0.062), (0.052, 0.018)]:
        jv, jn, ji = make_oriented_box(0.006, 0.010, 0.006, cx=px, cy=CENTER_Y + py, cz=z_center, angle=0.45)
        base = len(verts) // 3
        verts.extend(jv); norms.extend(jn); idxs.extend([idx + base for idx in ji])

    return verts, norms, idxs

# 12. Glucydur Balance Assembly & Hairspring
def create_balance_assembly(radius=0.078, z_center=0.004):
    verts, norms, idxs = [], [], []
    rv, rn, ri = make_ring(r_inner=0.068, r_outer=radius, height=0.004, z_center=z_center, segs=40)
    verts.extend(rv); norms.extend(rn); idxs.extend(ri)

    for i in range(3):
        angle = (i / 3.0) * math.pi * 2
        sv, sn, si = make_oriented_box(0.006, radius * 1.8, 0.003, cx=0.0, cy=CENTER_Y, cz=z_center, angle=angle)
        base = len(verts) // 3
        verts.extend(sv); norms.extend(sn); idxs.extend([idx + base for idx in si])

    for i in range(12):
        angle = (i / 12.0) * math.pi * 2
        sx = (radius + 0.003) * math.cos(angle)
        sy = CENTER_Y + (radius + 0.003) * math.sin(angle)
        tv, tn, ti = make_cylinder(0.002, 0.002, 0.005, z_center=z_center, segs=8, cx=sx, cy=sy)
        base = len(verts) // 3
        verts.extend(tv); norms.extend(tn); idxs.extend([idx + base for idx in ti])

    h_segs = 120
    h_turns = 5.0
    h_base = len(verts) // 3
    for s in range(h_segs):
        t = s / h_segs
        h_rad = 0.014 + t * 0.046
        theta = t * math.pi * 2 * h_turns
        hx = h_rad * math.cos(theta)
        hy = CENTER_Y + h_rad * math.sin(theta)
        verts.extend([hx, hy, z_center + 0.003])
        norms.extend(pack_normal(0, 0, 1))
        verts.extend([hx, hy, z_center + 0.005])
        norms.extend(pack_normal(0, 0, 1))
    for s in range(h_segs - 1):
        i0 = h_base + s * 2
        idxs.extend([i0, i0 + 2, i0 + 1, i0 + 2, i0 + 3, i0 + 1])

    return verts, norms, idxs

# 13. 4-Wheel Gear Train & Mainspring Barrel
def create_gear_train(z_center=-0.008):
    verts, norms, idxs = [], [], []
    gears = [
        ('barrel', 0.082, 0.012, -0.065, CENTER_Y + 0.045, 24),
        ('center', 0.065, 0.006, 0.0, CENTER_Y, 20),
        ('third', 0.052, 0.005, 0.055, CENTER_Y - 0.035, 18),
        ('fourth', 0.040, 0.004, -0.045, CENTER_Y - 0.055, 16)
    ]
    for name, r, h, gx, gy, teeth in gears:
        wv, wn, wi = make_cylinder(r, r, h, z_center=z_center, segs=32, cx=gx, cy=gy)
        base = len(verts) // 3
        verts.extend(wv); norms.extend(wn); idxs.extend([idx + base for idx in wi])
        for t in range(teeth):
            angle = (t / teeth) * math.pi * 2
            tx = gx + (r + 0.002) * math.cos(angle)
            ty = gy + (r + 0.002) * math.sin(angle)
            tv, tn, ti = make_oriented_box(0.003, 0.006, h, cx=tx, cy=ty, cz=z_center, angle=angle)
            base = len(verts) // 3
            verts.extend(tv); norms.extend(tn); idxs.extend([idx + base for idx in ti])

    return verts, norms, idxs

# 14. Column Wheel Chronograph Clutch
def create_column_wheel(radius=0.036, z_center=-0.016):
    verts, norms, idxs = [], [], []
    bv, bn, bi = make_cylinder(radius, radius, 0.006, z_center=z_center, segs=28, cx=0.065, cy=CENTER_Y + 0.065)
    verts.extend(bv); norms.extend(bn); idxs.extend(bi)

    for i in range(6):
        angle = (i / 6.0) * math.pi * 2
        px = 0.065 + (radius * 0.72) * math.cos(angle)
        py = CENTER_Y + 0.065 + (radius * 0.72) * math.sin(angle)
        pv, pn, pi = make_cylinder(0.0045, 0.0045, 0.012, z_center=z_center + 0.007, segs=12, cx=px, cy=py)
        base = len(verts) // 3
        verts.extend(pv); norms.extend(pn); idxs.extend([idx + base for idx in pi])

    return verts, norms, idxs

# 15. Mainplate & Jewel Bearings
def create_mainplate_bridges(radius=0.180, z_center=-0.030):
    verts, norms, idxs = [], [], []
    mv, mn, mi = make_cylinder(radius, radius, 0.014, z_center=z_center, segs=48)
    verts.extend(mv); norms.extend(mn); idxs.extend(mi)

    jewels = [
        (0.0, 0.0), (0.065, 0.065), (-0.065, 0.045), (0.055, -0.035),
        (-0.045, -0.055), (0.035, 0.035), (0.018, 0.062), (0.052, 0.018),
        (-0.08, -0.02), (0.08, -0.02), (0.0, -0.08), (0.0, 0.08)
    ]
    for jx, jy in jewels:
        jv, jn, ji = make_cylinder(0.006, 0.006, 0.004, z_center=z_center + 0.008, segs=12, cx=jx, cy=CENTER_Y + jy)
        base = len(verts) // 3
        verts.extend(jv); norms.extend(jn); idxs.extend([idx + base for idx in ji])

    return verts, norms, idxs

# 16. Heavy Tungsten Oscillating Rotor
def create_oscillating_rotor(radius=0.174, z_center=-0.044):
    verts, norms, idxs = [], [], []
    segs = 32
    w_base = len(verts) // 3
    for s in range(segs + 1):
        angle = (s / segs) * math.pi
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([radius * ca, CENTER_Y + radius * sa, z_center + 0.004])
        norms.extend(pack_normal(0, 0, 1))
        verts.extend([(radius - 0.032) * ca, CENTER_Y + (radius - 0.032) * sa, z_center + 0.004])
        norms.extend(pack_normal(0, 0, 1))
    for s in range(segs):
        i0 = w_base + s * 2
        idxs.extend([i0, i0 + 2, i0 + 1, i0 + 2, i0 + 3, i0 + 1])

    bv, bn, bi = make_ring(r_inner=0.012, r_outer=0.034, height=0.008, z_center=z_center, segs=24)
    base = len(verts) // 3
    verts.extend(bv); norms.extend(bn); idxs.extend([idx + base for idx in bi])

    return verts, norms, idxs

# 17. 316L Stainless Steel Watch Case with Ergonomic Sculpted Lugs, Crown & Pushers
def create_watch_case(radius=0.220, height=0.068, z_center=0.0):
    verts, norms, idxs = [], [], []
    cv, cn, ci = make_ring(r_inner=0.185, r_outer=radius, height=height, z_center=z_center, segs=54)
    verts.extend(cv); norms.extend(cn); idxs.extend(ci)

    # 4 Ergonomically Curved Lugs extending North (+Y) and South (-Y)
    lugs = [
        (0.125, CENTER_Y + 0.165, 0.110, CENTER_Y + 0.265, z_center + 0.010, z_center - 0.018),
        (-0.125, CENTER_Y + 0.165, -0.110, CENTER_Y + 0.265, z_center + 0.010, z_center - 0.018),
        (0.125, CENTER_Y - 0.165, 0.110, CENTER_Y - 0.265, z_center + 0.010, z_center - 0.018),
        (-0.125, CENTER_Y - 0.165, -0.110, CENTER_Y - 0.265, z_center + 0.010, z_center - 0.018),
    ]

    for rx, ry, tx, ty, rz, tz in lugs:
        mx, my, mz = (rx + tx) / 2.0, (ry + ty) / 2.0, (rz + tz) / 2.0
        l_len = math.hypot(tx - rx, ty - ry)
        l_ang = math.atan2(ty - ry, tx - rx) - math.pi / 2.0
        lv, ln, li = make_oriented_box(0.024, l_len, height * 0.82, cx=mx, cy=my, cz=mz, angle=l_ang)
        base = len(verts) // 3
        verts.extend(lv); norms.extend(ln); idxs.extend([idx + base for idx in li])

    # Solid Steel Integrated Bracelet End-Links (North and South between the lugs)
    for end_y_dir in [1.0, -1.0]:
        ey = CENTER_Y + (0.210 * end_y_dir)
        ez = z_center - 0.008
        ev, en, ei = make_oriented_box(0.180, 0.045, height * 0.65, cx=0.0, cy=ey, cz=ez, angle=0.0)
        base = len(verts) // 3
        verts.extend(ev); norms.extend(en); idxs.extend([idx + base for idx in ei])
        cl_v, cl_n, cl_i = make_oriented_box(0.080, 0.050, height * 0.72, cx=0.0, cy=ey, cz=ez + 0.003, angle=0.0)
        base = len(verts) // 3
        verts.extend(cl_v); norms.extend(cl_n); idxs.extend([idx + base for idx in cl_i])

    # Crown Guards at 3 o'clock
    for g_y in [0.026, -0.026]:
        gv, gn, gi = make_oriented_box(0.026, 0.018, height * 0.72, cx=radius + 0.012, cy=CENTER_Y + g_y, cz=z_center, angle=0.0)
        base = len(verts) // 3
        verts.extend(gv); norms.extend(gn); idxs.extend([idx + base for idx in gi])

    # Knurled Fluted Winding Crown at 3 o'clock
    crown_x = radius + 0.034
    cr_r = 0.018
    crv, crn, cri = make_cylinder(cr_r, cr_r, 0.024, z_center=z_center, segs=24, cx=crown_x, cy=CENTER_Y)
    for v_idx in range(len(crv) // 3):
        ox = crv[v_idx*3] - crown_x
        oy = crv[v_idx*3+1] - CENTER_Y
        oz = crv[v_idx*3+2] - z_center
        crv[v_idx*3] = crown_x + oz
        crv[v_idx*3+1] = CENTER_Y + oy
        crv[v_idx*3+2] = z_center - ox
        onx, ony, onz = crn[v_idx*3], crn[v_idx*3+1], crn[v_idx*3+2]
        crn[v_idx*3] = onz
        crn[v_idx*3+1] = ony
        crn[v_idx*3+2] = -onx
    base = len(verts) // 3
    verts.extend(crv); norms.extend(crn); idxs.extend([idx + base for idx in cri])

    # Dual Chronograph Pump Pushers at 2 o'clock and 4 o'clock
    for p_deg in [32, -32]:
        p_rad = math.radians(p_deg)
        ca, sa = math.cos(p_rad), math.sin(p_rad)
        px = (radius + 0.024) * ca
        py = CENTER_Y + (radius + 0.024) * sa
        p_ang = p_rad - math.pi / 2.0
        col_v, col_n, col_i = make_oriented_box(0.018, 0.024, 0.018, cx=px, cy=py, cz=z_center + 0.005, angle=p_ang)
        base = len(verts) // 3
        verts.extend(col_v); norms.extend(col_n); idxs.extend([idx + base for idx in col_i])
        cap_x = (radius + 0.038) * ca
        cap_y = CENTER_Y + (radius + 0.038) * sa
        cap_v, cap_n, cap_i = make_oriented_box(0.016, 0.014, 0.016, cx=cap_x, cy=cap_y, cz=z_center + 0.005, angle=p_ang)
        base = len(verts) // 3
        verts.extend(cap_v); norms.extend(cap_n); idxs.extend([idx + base for idx in cap_i])

    return verts, norms, idxs

# 18. Screw-Down Exhibition Caseback
def create_exhibition_caseback(radius=0.220, z_center=-0.040):
    verts, norms, idxs = [], [], []
    rv, rn, ri = make_ring(r_inner=0.150, r_outer=radius, height=0.012, z_center=z_center, segs=54)
    verts.extend(rv); norms.extend(rn); idxs.extend(ri)

    for i in range(6):
        angle = (i / 6.0) * math.pi * 2
        nx = 0.178 * math.cos(angle)
        ny = CENTER_Y + 0.178 * math.sin(angle)
        nv, nn, ni = make_oriented_box(0.009, 0.015, 0.006, cx=nx, cy=ny, cz=z_center - 0.004, angle=angle)
        base = len(verts) // 3
        verts.extend(nv); norms.extend(nn); idxs.extend([idx + base for idx in ni])

    return verts, norms, idxs

# 19. Rear Exhibition Sapphire Observation Window
def create_caseback_crystal(radius=0.152, z_center=-0.044):
    return make_cylinder(radius, radius, 0.004, z_center=z_center, segs=48)

def main():
    out_dir = Path(__file__).resolve().parent.parent / 'public' / 'models'
    out_dir.mkdir(parents=True, exist_ok=True)

    b = ChronoBuilder()
    print("Building 19-part luxury mechanical automatic chronograph with live ticking movement...")

    # Part 1: Front Sapphire Crystal
    v, n, i = create_sapphire_crystal()
    b.append_part('chrono_sapphire_crystal', 'Domed Sapphire Crystal', 'sapphire_crystal', 'sapphire_optics', v, n, i, [0.0, 0.0, 0.38])

    # Part 2: Ceramic Tachymeter Bezel
    v, n, i = create_tachymeter_bezel()
    b.append_part('chrono_tachymeter_bezel', 'Ceramic Tachymeter Bezel', 'tachymeter_bezel', 'tachymeter_bezel', v, n, i, [0.0, 0.0, 0.30])

    # Part 3: High-Contrast Rhodium Indices & Calibrations
    v, n, i = create_dial_indices()
    b.append_part('chrono_dial_indices', 'Applied Rhodium Batons & Tachymeter Scale', 'dial_indices', 'dial_indices', v, n, i, [0.0, 0.0, 0.25])

    # Part 4: Faceted Dauphine Hour Hand (Animated ticking clock)
    v, n, i = create_hour_hand()
    b.append_part('chrono_hour_hand', 'Faceted Dauphine Hour Hand', 'hands_assembly', 'hands_assembly', v, n, i, [0.0, 0.0, 0.21])

    # Part 5: Faceted Dauphine Minute Hand (Animated ticking clock)
    v, n, i = create_minute_hand()
    b.append_part('chrono_minute_hand', 'Faceted Dauphine Minute Hand', 'hands_assembly', 'hands_assembly', v, n, i, [0.0, 0.0, 0.22])

    # Part 6: Racing Red Chronograph Sweep Seconds (8-beat mechanical sweep!)
    v, n, i = create_chrono_sweeper()
    b.append_part('chrono_seconds_sweeper', 'Racing Red Chronograph Sweeper', 'chrono_sweeper', 'chrono_needle', v, n, i, [0.0, 0.0, 0.24])

    # Part 7: Small Running Seconds Hand at 9 o'clock (Continuous ticking)
    v, n, i = create_sub_seconds()
    b.append_part('chrono_sub_seconds', 'Small Running Seconds Hand', 'sub_seconds', 'hands_assembly', v, n, i, [-0.04, 0.0, 0.20])

    # Part 8: Sub-dial Counters & Pinion Collar (Static 30-min & 12-hr needles)
    v, n, i = create_sub_hands_static()
    b.append_part('chrono_sub_hands_static', 'Sub-dial Indicators & Pinion Cap', 'hands_assembly', 'hands_assembly', v, n, i, [0.02, -0.02, 0.19])

    # Part 9: Sunburst Obsidian Dial Plate
    v, n, i = create_dial_face()
    b.append_part('chrono_dial_face', 'Sunburst Tri-Compax Dial', 'dial_face', 'dial_face', v, n, i, [0.0, 0.0, 0.15])

    # Part 10: Escapement Wheel (Impulses 8 times per second)
    v, n, i = create_escapement_wheel()
    b.append_part('chrono_escapement_wheel', 'High-Beat Escape Wheel', 'escapement_wheel', 'regulating_organ', v, n, i, [0.04, 0.06, 0.09])

    # Part 11: Synthetic Ruby Pallet Lever (Rocks 8 times per second)
    v, n, i = create_pallet_fork()
    b.append_part('chrono_pallet_fork', 'Synthetic Ruby Pallet Lever', 'pallet_fork', 'regulating_organ', v, n, i, [0.08, 0.08, 0.07])

    # Part 12: Glucydur Balance Assembly & Hairspring (Oscillates at 4 Hz)
    v, n, i = create_balance_assembly()
    b.append_part('chrono_balance_assembly', 'Glucydur Balance & Hairspring', 'balance_wheel', 'regulating_organ', v, n, i, [-0.08, 0.06, 0.05])

    # Part 13: 4-Wheel Transmission Train
    v, n, i = create_gear_train()
    b.append_part('chrono_gear_train', '4-Wheel Transmission Train', 'gear_train', 'gear_transmission', v, n, i, [-0.04, -0.04, -0.02])

    # Part 14: 6-Pillar Chronograph Column Wheel
    v, n, i = create_column_wheel()
    b.append_part('chrono_column_wheel', '6-Pillar Chronograph Clutch', 'column_wheel', 'gear_transmission', v, n, i, [0.07, 0.04, -0.04])

    # Part 15: Mainplate & Jewel Bearings
    v, n, i = create_mainplate_bridges()
    b.append_part('chrono_mainplate_bridges', 'Perlage Mainplate & Jewel Bearings', 'mainplate', 'automatic_winding', v, n, i, [0.0, 0.0, -0.08])

    # Part 16: Heavy Tungsten Oscillating Rotor
    v, n, i = create_oscillating_rotor()
    b.append_part('chrono_oscillating_rotor', 'Heavy Tungsten Bidirectional Rotor', 'oscillating_rotor', 'automatic_winding', v, n, i, [0.0, -0.06, -0.15])

    # Part 17: 316L Stainless Steel Watch Case with Ergonomic Lugs & Pushers
    v, n, i = create_watch_case()
    b.append_part('chrono_watch_case', '316L Cushion Watch Case & Pushers', 'watch_case', 'case_exterior', v, n, i, [0.0, 0.0, -0.22])

    # Part 18: Screw-Down Exhibition Caseback
    v, n, i = create_exhibition_caseback()
    b.append_part('chrono_exhibition_caseback', 'Screw-Down Exhibition Caseback', 'caseback', 'case_exterior', v, n, i, [0.0, 0.0, -0.28])

    # Part 19: Rear Sapphire Crystal
    v, n, i = create_caseback_crystal()
    b.append_part('chrono_caseback_crystal', 'Rear Exhibition Crystal', 'caseback_crystal', 'sapphire_optics', v, n, i, [0.0, 0.0, -0.34])

    bin_filename = 'chronograph-0.bin'
    bin_path = out_dir / bin_filename
    bin_path.write_bytes(b.blob)
    print(f"Wrote binary: {bin_path} ({len(b.blob):,} bytes, {b.total_triangles:,} triangles)")

    systems = [
        {
            'id': 'case_exterior',
            'name': '316L Stainless Steel Case & Pushers',
            'color': '#c4ccd4',
            'description': '316L stainless steel case featuring 4 sculpted ergonomic curved lugs, integrated bracelet end-links, knurled screw-down winding crown, crown guards, and dual pump pushers.'
        },
        {
            'id': 'tachymeter_bezel',
            'name': 'Ceramic Tachymeter Bezel',
            'color': '#16191d',
            'description': 'High-gloss obsidian black ceramic bezel insert framed by a polished 316L retaining ring, carrying radial tachymetric velocity calibrations.'
        },
        {
            'id': 'sapphire_optics',
            'name': 'Anti-Reflective Sapphire Crystal',
            'color': '#d4e6f6',
            'description': 'Domed synthetic corundum sapphire crystal (Mohs hardness 9) providing scratch-proof optical clarity and anti-reflective protection.'
        },
        {
            'id': 'dial_indices',
            'name': 'Applied Rhodium Batons & Scales',
            'color': '#f0f4f8',
            'description': 'Precision 3D faceted rhodium hour batons with luminous inlays, 60-second outer chapter track ticks, sub-dial rings, and ceramic tachymeter calibration markings.'
        },
        {
            'id': 'hands_assembly',
            'name': 'Faceted Dauphine Hands & Pinions',
            'color': '#e8edf2',
            'description': 'Faceted Dauphine hour and minute hands capturing specular light with beveled ridges, paired with small seconds running needle and pinion collar.'
        },
        {
            'id': 'chrono_needle',
            'name': 'Racing Red Chronograph Sweeper',
            'color': '#e6282b',
            'description': 'Ultra-slender central chronograph sweep seconds needle finished in vibrant racing scarlet, sweeping smoothly at 8 beats per second with counterweight and arrow tip.'
        },
        {
            'id': 'dial_face',
            'name': 'Sunburst Obsidian Dial',
            'color': '#15181b',
            'description': "Sunburst obsidian dial face with 3 recessed circular sub-dial pans at 3, 6, and 9 o'clock for 30-minute, 12-hour, and running seconds chronograph readouts."
        },
        {
            'id': 'regulating_organ',
            'name': '28,800 vph Escapement & Balance',
            'color': '#e5b74c',
            'description': 'The heart of the movement: a 28,800 vph (4 Hz) club-tooth escape wheel, synthetic ruby pallet lever, and Glucydur balance wheel with Nivarox hairspring.'
        },
        {
            'id': 'gear_transmission',
            'name': 'Gear Train & 6-Pillar Column Wheel',
            'color': '#d69f3a',
            'description': 'Precision brass gear train transmitting mainspring torque, paired with a 6-pillar micro-machined column wheel clutch coordinating instant start, stop, and reset actions.'
        },
        {
            'id': 'automatic_winding',
            'name': 'Heavy Tungsten Rotor & Mainplate',
            'color': '#828e9a',
            'description': 'Heavy tungsten bidirectional oscillating rotor winding the mainspring via wrist motion, supported by a circular perlage mainplate with 28 synthetic ruby jewels.'
        }
    ]

    concepts = [
        {'id': 'sapphire_crystal', 'name': 'Domed Sapphire Crystal', 'elements': ['chrono_sapphire_crystal']},
        {'id': 'tachymeter_bezel', 'name': 'Ceramic Tachymeter Bezel', 'elements': ['chrono_tachymeter_bezel']},
        {'id': 'dial_indices', 'name': 'Applied Rhodium Batons & Scales', 'elements': ['chrono_dial_indices']},
        {'id': 'hour_hand', 'name': 'Faceted Dauphine Hour Hand', 'elements': ['chrono_hour_hand']},
        {'id': 'minute_hand', 'name': 'Faceted Dauphine Minute Hand', 'elements': ['chrono_minute_hand']},
        {'id': 'chrono_sweeper', 'name': 'Racing Red Chronograph Sweeper', 'elements': ['chrono_seconds_sweeper']},
        {'id': 'sub_seconds', 'name': 'Small Running Seconds Hand', 'elements': ['chrono_sub_seconds']},
        {'id': 'sub_hands_static', 'name': 'Sub-dial Indicators & Pinion Cap', 'elements': ['chrono_sub_hands_static']},
        {'id': 'dial_face', 'name': 'Sunburst Tri-Compax Dial', 'elements': ['chrono_dial_face']},
        {'id': 'escapement_wheel', 'name': 'High-Beat Escape Wheel', 'elements': ['chrono_escapement_wheel']},
        {'id': 'pallet_fork', 'name': 'Synthetic Ruby Pallet Lever', 'elements': ['chrono_pallet_fork']},
        {'id': 'balance_wheel', 'name': 'Glucydur Balance & Hairspring', 'elements': ['chrono_balance_assembly']},
        {'id': 'gear_train', 'name': '4-Wheel Transmission Train', 'elements': ['chrono_gear_train']},
        {'id': 'column_wheel', 'name': '6-Pillar Chronograph Clutch', 'elements': ['chrono_column_wheel']},
        {'id': 'mainplate', 'name': 'Perlage Mainplate & Jewel Bearings', 'elements': ['chrono_mainplate_bridges']},
        {'id': 'oscillating_rotor', 'name': 'Heavy Tungsten Bidirectional Rotor', 'elements': ['chrono_oscillating_rotor']},
        {'id': 'watch_case', 'name': '316L Cushion Watch Case & Pushers', 'elements': ['chrono_watch_case']},
        {'id': 'caseback', 'name': 'Screw-Down Exhibition Caseback', 'elements': ['chrono_exhibition_caseback']},
        {'id': 'caseback_crystal', 'name': 'Rear Exhibition Crystal', 'elements': ['chrono_caseback_crystal']},
    ]

    explanations = {
        'domed sapphire crystal': 'Ultra-pure synthetic corundum sapphire crystal (Mohs hardness 9) ground with a subtle outer dome. Anti-reflective coatings ensure pristine dial legibility.',
        'ceramic tachymeter bezel': 'High-gloss ceramic tachymeter bezel insert framed by polished 316L stainless steel, calibrated from 500 down to 60 units per hour for velocity calculation.',
        'applied rhodium batons & scales': 'Faceted 3D rhodium hour batons with white luminous inlays, paired with a 60-second chapter track, sub-dial rings, and radial tachymeter markings.',
        'faceted dauphine hour hand': 'Faceted Dauphine hour hand capturing specular light with beveled 3D center ridges, pointing to current local hour.',
        'faceted dauphine minute hand': 'Faceted Dauphine minute hand advancing in real time with beveled specular ridges for high optical legibility.',
        'racing red chronograph sweeper': 'Slender central sweep seconds hand finished in racing red with a classic counterweight and arrowhead tip, sweeping continuously at 8 beats per second (28,800 vph).',
        'small running seconds hand': 'Sub-dial running seconds needle at 9 o\'clock rotating continuously every 60 seconds to confirm movement operation.',
        'sub-dial indicators & pinion cap': 'Miniature sub-dial totalizer hands for 30-minute and 12-hour chronograph registers, capped by a central polished steel pinion collar.',
        'sunburst tri-compax dial': 'Obsidian dial plate featuring 3 recessed sub-dials: 30-minute counter at 3, 12-hour totalizer at 6, and running small seconds at 9.',
        'high-beat escape wheel': 'Specialized 15 club-tooth escape wheel running at 28,800 vibrations per hour (4 Hz), impulsing the balance 8 times per second.',
        'synthetic ruby pallet lever': 'Precision-balanced Swiss lever holding two synthetic ruby pallets that alternately lock and release the escape wheel with minimal horological friction.',
        'glucydur balance & hairspring': 'Temperature-stable beryllium-bronze Glucydur balance wheel paired with an 8-coil Nivarox hairspring oscillating at 4 Hz for isochronous timing precision.',
        '4-wheel transmission train': 'Horological brass gear train (mainspring barrel, center wheel, third wheel, and fourth wheel) stepping down mainspring torque to the escapement.',
        '6-pillar chronograph clutch': 'Classic column wheel clutch with 6 precision-machined steel pillars mechanically coordinating instant start, stop, and reset pusher actions.',
        'perlage mainplate & jewel bearings': 'Circular-grained (perlage) brass mainplate providing micro-tolerance alignment for 28 synthetic ruby jewel bearings.',
        'heavy tungsten bidirectional rotor': 'High-density tungsten oscillating weight that rotates smoothly with wrist movement to wind the mainspring via a reduction reverser gear train.',
        '316l cushion watch case & pushers': '316L stainless steel case with 4 sculpted ergonomic lugs, integrated bracelet end-links, fluted crown, crown guards, and dual chronograph pump pushers.',
        'screw-down exhibition caseback': 'Threaded 316L caseback bezel holding the rear observation window, engraved with 6 precision wrench notches for hermetic water-resistant sealing.',
        'rear exhibition crystal': 'Flat synthetic sapphire window in the caseback allowing owners to admire the operating column wheel, balance oscillation, and oscillating rotor.'
    }

    atlas_json = {
        'version': '1.0.0',
        'itemName': 'Mechanical Automatic Chronograph',
        'subtitle': '28-Jewel Column-Wheel Automatic Chronograph Timepiece',
        'source': 'Precision Horology CAD Studio',
        'scope': 'Complete Micro-Mechanical Movement & 316L Case Assembly',
        'parts': b.parts,
        'concepts': concepts,
        'systems': systems,
        'explanations': explanations,
        'presets': [
            {'name': 'Complete Watch', 'systems': [s['id'] for s in systems]},
            {'name': 'Dial & Hands', 'systems': ['dial_face', 'dial_indices', 'hands_assembly', 'chrono_needle', 'sapphire_optics', 'tachymeter_bezel']},
            {'name': 'Chronograph Movement', 'systems': ['regulating_organ', 'gear_transmission', 'automatic_winding']},
            {'name': '316L Case & Pushers', 'systems': ['case_exterior', 'tachymeter_bezel', 'sapphire_optics']}
        ],
        'chunks': [
            {
                'url': f'/models/{bin_filename}',
                'bytes': len(b.blob)
            }
        ],
        'triangles': b.total_triangles
    }

    json_path = out_dir / 'chronograph.json'
    json_path.write_text(json.dumps(atlas_json, indent=2))
    print(f"Wrote metadata: {json_path}")
    print(f"Total parts: {len(b.parts)}, total triangles: {b.total_triangles:,}")

    render_screen_check(atlas_json, b.blob)

def render_screen_check(atlas, buf):
    width, height = 750, 750
    zbuffer = [-1e9] * (width * height)
    img = [bytearray([242, 243, 243]) for _ in range(width * height)]

    colors = {
        'case_exterior': (195, 202, 208),
        'tachymeter_bezel': (24, 28, 32),
        'dial_face': (18, 22, 26),
        'dial_indices': (248, 250, 253),
        'hands_assembly': (236, 240, 245),
        'chrono_needle': (228, 38, 42),
        'regulating_organ': (228, 182, 82),
        'gear_transmission': (212, 158, 56),
        'automatic_winding': (128, 141, 152),
        'sapphire_optics': None
    }

    # Pre-calculated sample angles for visual snapshot:
    # 10:10:36 clock time snapshot
    hand_rotations = {
        'chrono_hour_hand': (0.0, CENTER_Y, -math.radians(305)),      # 10 o'clock
        'chrono_minute_hand': (0.0, CENTER_Y, -math.radians(60)),     # 10 past
        'chrono_seconds_sweeper': (0.0, CENTER_Y, -math.radians(216)), # 36 seconds
        'chrono_sub_seconds': (-0.076, CENTER_Y, -math.radians(216)),  # 36 seconds
        'chrono_balance_assembly': (0.0, CENTER_Y, 1.2),              # Oscillating
        'chrono_escapement_wheel': (0.0, CENTER_Y, -0.4),             # Stepping
        'chrono_pallet_fork': (0.035, CENTER_Y + 0.035, 0.06),        # Ticking
    }

    fov = 34.0 * math.pi / 180.0
    f = (height / 2.0) / math.tan(fov / 2.0)
    cam_dist = 2.4
    rot_y = 0.40
    rot_x = 0.15

    cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
    cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)

    lx, ly, lz = -0.4, 0.7, 0.6
    ll = math.hypot(lx, ly, lz)
    lx, ly, lz = lx/ll, ly/ll, lz/ll

    def transform(x, y, z):
        y = y - CENTER_Y
        rx = x * cos_y + z * sin_y
        rz = -x * sin_y + z * cos_y
        ry = y * cos_x - rz * sin_x
        rz = y * sin_x + rz * cos_x
        cz = rz - cam_dist
        px = width / 2.0 + (rx / -cz) * f
        py = height / 2.0 - (ry / -cz) * f
        return px, py, cz, rx, ry, rz

    def edge_fn(ax, ay, bx, by, cx, cy):
        return (cx - ax) * (by - ay) - (cy - ay) * (bx - ax)

    for p in atlas['parts']:
        sys_id = p['system']
        base_col = colors.get(sys_id)
        if base_col is None:
            continue

        part_id = p['id']
        rot_spec = hand_rotations.get(part_id)

        v_count = p['vertexCount']
        i_count = p['indexCount']
        verts = list(struct.unpack_from(f'<{v_count * 3}f', buf, p['positions']))
        idxs = struct.unpack_from(f'<{i_count}I', buf, p['indices'])

        # Apply part rotation if configured
        if rot_spec:
            px, py, ang = rot_spec
            ca, sa = math.cos(ang), math.sin(ang)
            for v_i in range(v_count):
                vx = verts[v_i * 3]
                vy = verts[v_i * 3 + 1]
                rx = px + (vx - px) * ca - (vy - py) * sa
                ry = py + (vx - px) * sa + (vy - py) * ca
                verts[v_i * 3] = rx
                verts[v_i * 3 + 1] = ry

        for tri in range(0, len(idxs), 3):
            i0, i1, i2 = idxs[tri], idxs[tri+1], idxs[tri+2]
            x0, y0, z0 = verts[i0*3], verts[i0*3+1], verts[i0*3+2]
            x1, y1, z1 = verts[i1*3], verts[i1*3+1], verts[i1*3+2]
            x2, y2, z2 = verts[i2*3], verts[i2*3+1], verts[i2*3+2]

            p0 = transform(x0, y0, z0)
            p1 = transform(x1, y1, z1)
            p2 = transform(x2, y2, z2)

            vax, vay, vaz = p1[3] - p0[3], p1[4] - p0[4], p1[5] - p0[5]
            vbx, vby, vbz = p2[3] - p0[3], p2[4] - p0[4], p2[5] - p0[5]
            nx = vay * vbz - vaz * vby
            ny = vaz * vbx - vax * vbz
            nz = vax * vby - vay * vbx
            nl = math.hypot(nx, ny, nz)
            if nl < 1e-8:
                continue
            nx, ny, nz = nx/nl, ny/nl, nz/nl

            diffuse = max(0.15, nx * lx + ny * ly + nz * lz)
            half_x, half_y, half_z = lx, ly, lz + 1.0
            hl = math.hypot(half_x, half_y, half_z)
            spec = max(0.0, (nx * (half_x/hl) + ny * (half_y/hl) + nz * (half_z/hl))) ** 16

            r = min(255, int(base_col[0] * (0.35 + 0.65 * diffuse) + 70 * spec))
            g = min(255, int(base_col[1] * (0.35 + 0.65 * diffuse) + 70 * spec))
            b = min(255, int(base_col[2] * (0.35 + 0.65 * diffuse) + 70 * spec))

            min_x = max(0, int(math.floor(min(p0[0], p1[0], p2[0]))))
            max_x = min(width - 1, int(math.ceil(max(p0[0], p1[0], p2[0]))))
            min_y = max(0, int(math.floor(min(p0[1], p1[1], p2[1]))))
            max_y = min(height - 1, int(math.ceil(max(p0[1], p1[1], p2[1]))))

            area = edge_fn(p0[0], p0[1], p1[0], p1[1], p2[0], p2[1])
            if abs(area) < 1e-5:
                continue

            for py_i in range(min_y, max_y + 1):
                for px_i in range(min_x, max_x + 1):
                    w0 = edge_fn(p1[0], p1[1], p2[0], p2[1], px_i + 0.5, py_i + 0.5)
                    w1 = edge_fn(p2[0], p2[1], p0[0], p0[1], px_i + 0.5, py_i + 0.5)
                    w2 = edge_fn(p0[0], p0[1], p1[0], p1[1], px_i + 0.5, py_i + 0.5)

                    if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                        bc0 = w0 / area
                        bc1 = w1 / area
                        bc2 = w2 / area
                        depth = bc0 * p0[2] + bc1 * p1[2] + bc2 * p2[2]

                        idx = py_i * width + px_i
                        if depth > zbuffer[idx]:
                            zbuffer[idx] = depth
                            img[idx][0] = r
                            img[idx][1] = g
                            img[idx][2] = b

    # Stationary floor pedestal
    pedestal_screen_y = int(height / 2.0 - ((-0.25) / cam_dist) * f)
    for py in range(pedestal_screen_y - 12, min(height, pedestal_screen_y + 120)):
        for px in range(width):
            dx = (px - width / 2.0) / 280.0
            dy = (py - (pedestal_screen_y + 50)) / 35.0
            if dx*dx + dy*dy <= 1.0:
                idx = py * width + px
                if zbuffer[idx] < -cam_dist:
                    for c_i in range(3):
                        img[idx][c_i] = int(img[idx][c_i] * 0.94)

    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)
        for x in range(width):
            raw_data.extend(img[y * width + x])

    def make_png(w, h, rgb_bytes):
        def chunk(tag, data):
            c = tag + data
            crc = zlib.crc32(c) & 0xffffffff
            return struct.pack('>I', len(data)) + c + struct.pack('>I', crc)
        hdr = bytes([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
        ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
        idat = chunk(b'IDAT', zlib.compress(rgb_bytes, 9))
        iend = chunk(b'IEND', b'')
        return hdr + ihdr + idat + iend

    png_bytes = make_png(width, height, raw_data)
    root_dir = Path(__file__).resolve().parent.parent
    screen_check_path = root_dir / 'screen_check.png'
    screen_check_path.write_bytes(png_bytes)
    print(f"Saved screen_check.png successfully ({len(png_bytes):,} bytes)!")

if __name__ == '__main__':
    main()
