"""Procedural 3D Geometry Generator for Apple EarPods Gadget Deconstruction.
Generates 21 distinct engineered parts, compiles binary chunk buffers with 16-bit signed normals,
and outputs earpods.json and earpods-0.bin.
"""
import sys, json, math, struct
from pathlib import Path
from array import array

root = Path(__file__).resolve().parents[1]
out_dir = root / 'public/models'
out_dir.mkdir(parents=True, exist_ok=True)

class MeshBuilder:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.indices = []
        self.parts = []
        self.blob = bytearray()
        self.total_triangles = 0

    def append_part(self, part_id, name, concept_id, system, verts, norms, idxs):
        po = len(self.blob)
        while po % 4:
            self.blob.append(0)
            po += 1
        self.blob.extend(array('f', verts).tobytes())

        no = len(self.blob)
        while no % 4:
            self.blob.append(0)
            no += 1
        self.blob.extend(array('h', norms).tobytes())

        io = len(self.blob)
        while io % 4:
            self.blob.append(0)
            io += 1
        self.blob.extend(array('I', idxs).tobytes())

        xs = verts[0::3]
        ys = verts[1::3]
        zs = verts[2::3]
        bounds = [[min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]]
        v_count = len(verts) // 3
        i_count = len(idxs)
        self.total_triangles += i_count // 3

        self.parts.append({
            'id': part_id,
            'name': name,
            'conceptId': concept_id,
            'system': system,
            'chunk': 0,
            'positions': po,
            'normals': no,
            'indices': io,
            'vertexCount': v_count,
            'indexCount': i_count,
            'bounds': bounds
        })

# --- GEOMETRY GENERATORS ---

def create_cylinder(radius_top, radius_bottom, height, segments, center=(0, 0, 0), cap_top=True, cap_bottom=True):
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    half_h = height / 2.0
    
    slant = math.atan2(radius_bottom - radius_top, height)
    cos_s = math.cos(slant)
    sin_s = math.sin(slant)

    for i in range(segments + 1):
        u = i / segments
        angle = u * math.pi * 2
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        nx = cos_a * cos_s
        ny = sin_s
        nz = sin_a * cos_s

        verts.extend([cx + radius_top * cos_a, cy + half_h, cz + radius_top * sin_a])
        norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])

        verts.extend([cx + radius_bottom * cos_a, cy - half_h, cz + radius_bottom * sin_a])
        norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])

    for i in range(segments):
        i0 = i * 2
        i1 = i0 + 1
        i2 = (i + 1) * 2
        i3 = i2 + 1
        idxs.extend([i0, i1, i2, i2, i1, i3])

    if cap_top and radius_top > 0:
        base = len(verts) // 3
        verts.extend([cx, cy + half_h, cz])
        norms.extend([0, 32767, 0])
        for i in range(segments + 1):
            angle = (i / segments) * math.pi * 2
            verts.extend([cx + radius_top * math.cos(angle), cy + half_h, cz + radius_top * math.sin(angle)])
            norms.extend([0, 32767, 0])
        for i in range(segments):
            idxs.extend([base, base + 1 + i, base + 2 + i])

    if cap_bottom and radius_bottom > 0:
        base = len(verts) // 3
        verts.extend([cx, cy - half_h, cz])
        norms.extend([0, -32767, 0])
        for i in range(segments + 1):
            angle = (i / segments) * math.pi * 2
            verts.extend([cx + radius_bottom * math.cos(angle), cy - half_h, cz + radius_bottom * math.sin(angle)])
            norms.extend([0, -32767, 0])
        for i in range(segments):
            idxs.extend([base, base + 2 + i, base + 1 + i])

    return verts, norms, idxs

def create_ring(r_inner, r_outer, height, segments, center=(0, 0, 0)):
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    half_h = height / 2.0

    for i in range(segments + 1):
        angle = (i / segments) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_outer * ca, cy + half_h, cz + r_outer * sa])
        norms.extend([round(ca * 32767), 0, round(sa * 32767)])
        verts.extend([cx + r_outer * ca, cy - half_h, cz + r_outer * sa])
        norms.extend([round(ca * 32767), 0, round(sa * 32767)])
    for i in range(segments):
        i0 = i * 2
        i1 = i0 + 1
        i2 = (i + 1) * 2
        i3 = i2 + 1
        idxs.extend([i0, i1, i2, i2, i1, i3])

    base_in = len(verts) // 3
    for i in range(segments + 1):
        angle = (i / segments) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_inner * ca, cy + half_h, cz + r_inner * sa])
        norms.extend([round(-ca * 32767), 0, round(-sa * 32767)])
        verts.extend([cx + r_inner * ca, cy - half_h, cz + r_inner * sa])
        norms.extend([round(-ca * 32767), 0, round(-sa * 32767)])
    for i in range(segments):
        i0 = base_in + i * 2
        i1 = i0 + 1
        i2 = base_in + (i + 1) * 2
        i3 = i2 + 1
        idxs.extend([i0, i2, i1, i2, i3, i1])

    base_top = len(verts) // 3
    for i in range(segments + 1):
        angle = (i / segments) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_outer * ca, cy + half_h, cz + r_outer * sa])
        norms.extend([0, 32767, 0])
        verts.extend([cx + r_inner * ca, cy + half_h, cz + r_inner * sa])
        norms.extend([0, 32767, 0])
    for i in range(segments):
        i0 = base_top + i * 2
        i1 = i0 + 1
        i2 = base_top + (i + 1) * 2
        i3 = i2 + 1
        idxs.extend([i0, i1, i2, i2, i1, i3])

    base_bot = len(verts) // 3
    for i in range(segments + 1):
        angle = (i / segments) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + r_outer * ca, cy - half_h, cz + r_outer * sa])
        norms.extend([0, -32767, 0])
        verts.extend([cx + r_inner * ca, cy - half_h, cz + r_inner * sa])
        norms.extend([0, -32767, 0])
    for i in range(segments):
        i0 = base_bot + i * 2
        i1 = i0 + 1
        i2 = base_bot + (i + 1) * 2
        i3 = i2 + 1
        idxs.extend([i0, i2, i1, i2, i3, i1])

    return verts, norms, idxs

def create_torus(r_major, r_minor, seg_radial, seg_tubular, center=(0, 0, 0), arc=math.pi*2):
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    for i in range(seg_radial + 1):
        u = (i / seg_radial) * arc
        cu, su = math.cos(u), math.sin(u)
        for j in range(seg_tubular + 1):
            v = (j / seg_tubular) * math.pi * 2
            cv, sv = math.cos(v), math.sin(v)
            px = (r_major + r_minor * cv) * cu
            pz = (r_major + r_minor * cv) * su
            py = r_minor * sv
            nx = cv * cu
            nz = cv * su
            ny = sv
            verts.extend([cx + px, cy + py, cz + pz])
            norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])
    stride = seg_tubular + 1
    for i in range(seg_radial):
        for j in range(seg_tubular):
            i0 = i * stride + j
            i1 = (i + 1) * stride + j
            i2 = (i + 1) * stride + (j + 1)
            i3 = i * stride + (j + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])
    return verts, norms, idxs

def create_dome(radius, height, rings, segments, center=(0, 0, 0), inverted=False):
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    sign = -1.0 if inverted else 1.0

    for r in range(rings + 1):
        v = r / rings
        phi = v * (math.pi / 2.0)
        y = math.sin(phi) * height * sign
        rad = math.cos(phi) * radius

        for s in range(segments + 1):
            u = s / segments
            theta = u * math.pi * 2
            x = rad * math.cos(theta)
            z = rad * math.sin(theta)
            nx = math.cos(phi) * math.cos(theta)
            ny = math.sin(phi) * sign
            nz = math.cos(phi) * math.sin(theta)
            verts.extend([cx + x, cy + y, cz + z])
            norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])

    stride = segments + 1
    for r in range(rings):
        for s in range(segments):
            i0 = r * stride + s
            i1 = (r + 1) * stride + s
            i2 = (r + 1) * stride + (s + 1)
            i3 = r * stride + (s + 1)
            if inverted:
                idxs.extend([i0, i2, i1, i0, i3, i2])
            else:
                idxs.extend([i0, i1, i2, i0, i2, i3])
    return verts, norms, idxs

def create_box(w, h, d, center=(0, 0, 0)):
    cx, cy, cz = center
    hw, hh, hd = w / 2.0, h / 2.0, d / 2.0
    faces = [
        ([cx-hw, cy-hh, cz+hd, cx+hw, cy-hh, cz+hd, cx+hw, cy+hh, cz+hd, cx-hw, cy+hh, cz+hd], [0, 0, 1]),
        ([cx+hw, cy-hh, cz-hd, cx-hw, cy-hh, cz-hd, cx-hw, cy+hh, cz-hd, cx+hw, cy+hh, cz-hd], [0, 0, -1]),
        ([cx-hw, cy+hh, cz+hd, cx+hw, cy+hh, cz+hd, cx+hw, cy+hh, cz-hd, cx-hw, cy+hh, cz-hd], [0, 1, 0]),
        ([cx-hw, cy-hh, cz-hd, cx+hw, cy-hh, cz-hd, cx+hw, cy-hh, cz+hd, cx-hw, cy-hh, cz+hd], [0, -1, 0]),
        ([cx+hw, cy-hh, cz+hd, cx+hw, cy-hh, cz-hd, cx+hw, cy+hh, cz-hd, cx+hw, cy+hh, cz+hd], [1, 0, 0]),
        ([cx-hw, cy-hh, cz-hd, cx-hw, cy-hh, cz+hd, cx-hw, cy+hh, cz+hd, cx-hw, cy+hh, cz-hd], [-1, 0, 0]),
    ]
    verts, norms, idxs = [], [], []
    for quad, (nx, ny, nz) in faces:
        base = len(verts) // 3
        for i in range(4):
            verts.extend(quad[i*3:(i+1)*3])
            norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])
        idxs.extend([base, base + 1, base + 2, base, base + 2, base + 3])
    return verts, norms, idxs

def create_lofted_housing(scale=1.0, center=(0, 0.85, 0)):
    verts, norms, idxs = [], [], []
    cx, cy, cz = center

    slices = [
        (0.18, 0.05, 0.11, 0.12, 1.0, 1.1),
        (0.15, 0.045, 0.14, 0.15, 1.05, 1.1),
        (0.11, 0.03, 0.18, 0.20, 1.1, 1.05),
        (0.06, 0.015, 0.21, 0.23, 1.12, 1.0),
        (0.00, 0.00, 0.23, 0.24, 1.12, 0.95),
        (-0.05, -0.015, 0.22, 0.23, 1.1, 0.9),
        (-0.10, -0.03, 0.19, 0.20, 1.05, 0.85),
        (-0.14, -0.04, 0.14, 0.14, 1.0, 0.8),
        (-0.18, -0.045, 0.08, 0.08, 0.9, 0.8),
    ]
    segments = 32

    for r_idx, (y_rel, z_rel, rx, rz, def_x, def_z) in enumerate(slices):
        for s in range(segments + 1):
            u = s / segments
            theta = u * math.pi * 2
            asym_x = (1.0 + 0.18 * math.cos(theta)) * def_x
            asym_z = (1.0 - 0.12 * math.sin(theta)) * def_z

            px = rx * math.cos(theta) * asym_x * scale
            py = (y_rel * scale)
            pz = (z_rel + rz * math.sin(theta) * asym_z) * scale

            nx = math.cos(theta) * 0.85
            ny = 0.4 if r_idx < 4 else -0.4
            nz = math.sin(theta) * 0.85
            l = math.hypot(nx, ny, nz) or 1.0
            nx, ny, nz = nx/l, ny/l, nz/l

            verts.extend([cx + px, cy + py, cz + pz])
            norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])

    stride = segments + 1
    for r in range(len(slices) - 1):
        for s in range(segments):
            i0 = r * stride + s
            i1 = (r + 1) * stride + s
            i2 = (r + 1) * stride + (s + 1)
            i3 = r * stride + (s + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_wire_helix(r_wire, r_helix, pitch, turns, segments_per_turn, center=(0, 0, 0)):
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    total_steps = int(turns * segments_per_turn)
    tube_segs = 8

    path_points = []
    for step in range(total_steps + 1):
        t = step / segments_per_turn
        angle = t * math.pi * 2
        px = cx + r_helix * math.cos(angle)
        pz = cz + r_helix * math.sin(angle)
        py = cy + t * pitch
        path_points.append((px, py, pz, angle))

    for pt_idx, (px, py, pz, angle) in enumerate(path_points):
        tang_x = -math.sin(angle)
        tang_z = math.cos(angle)
        norm_x = math.cos(angle)
        norm_z = math.sin(angle)

        for s in range(tube_segs + 1):
            phi = (s / tube_segs) * math.pi * 2
            c_phi, s_phi = math.cos(phi), math.sin(phi)
            vx = px + (norm_x * c_phi) * r_wire
            vy = py + s_phi * r_wire
            vz = pz + (norm_z * c_phi) * r_wire

            nx = norm_x * c_phi
            ny = s_phi
            nz = norm_z * c_phi
            verts.extend([vx, vy, vz])
            norms.extend([round(nx * 32767), round(ny * 32767), round(nz * 32767)])

    stride = tube_segs + 1
    for i in range(total_steps):
        for j in range(tube_segs):
            i0 = i * stride + j
            i1 = (i + 1) * stride + j
            i2 = (i + 1) * stride + (j + 1)
            i3 = i * stride + (j + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def main():
    mb = MeshBuilder()

    systems = [
        {'id': 'enclosure', 'name': 'Acoustic Enclosure', 'color': '#e2e8f0', 'description': 'The sculpted white polycarbonate housing. Modeled after 3D ear geometry for an ergonomic, non-intrusive concha fit without needing silicone ear tips.'},
        {'id': 'acoustic_tuning', 'name': 'Acoustic Tuning & Ports', 'color': '#475569', 'description': 'Micro-mesh grilles and precision acoustic vents. Tunes Helmholtz resonance, back-pressure damping, and directional sound delivery.'},
        {'id': 'transducer', 'name': 'Transducer & Driver', 'color': '#d97706', 'description': 'The 14.2mm dynamic speaker driver engine. Uses a high-compliance composite polymer diaphragm and copper voice coil to convert electrical signals into pristine sound.'},
        {'id': 'magnetic_circuit', 'name': 'Magnetic Motor', 'color': '#0284c7', 'description': 'High-flux Neodymium-Iron-Boron (NdFeB) magnet and high-permeability steel yoke, producing an intense focused magnetic gap for high acoustic sensitivity.'},
        {'id': 'electronics', 'name': 'Wiring & Terminals', 'color': '#10b981', 'description': 'Polyimide flex circuit board, gold solder pads, and oxygen-free copper litz wiring transmitting analog audio current with zero signal degradation.'},
        {'id': 'controls', 'name': 'Cable & Remote', 'color': '#8b5cf6', 'description': 'Flexible TPE cable with Kevlar core, strain relief boot, and inline remote with silicone MEMS microphone for Siri and crystal-clear hands-free calling.'},
    ]

    base_center = (0.0, 0.85, 0.0)
    bc_x, bc_y, bc_z = base_center

    # 1. Front Ergonomic Nozzle Cap (enclosure)
    v, n, i = create_cylinder(0.12, 0.17, 0.12, 32, center=(bc_x, bc_y + 0.13, bc_z + 0.07), cap_top=False, cap_bottom=False)
    mb.append_part('ep_front_nozzle', 'Ergonomic Front Nozzle Shell', 'concept_front_housing', 'enclosure', v, n, i)

    # 2. Main Sound Outlet Stainless Mesh (acoustic_tuning)
    v, n, i = create_cylinder(0.118, 0.118, 0.008, 32, center=(bc_x, bc_y + 0.19, bc_z + 0.07), cap_top=True, cap_bottom=True)
    mb.append_part('ep_main_grille', 'Main Sound Outlet Stainless Mesh', 'concept_acoustic_grilles', 'acoustic_tuning', v, n, i)

    # 3. Driver Sealing O-Ring Gasket (acoustic_tuning)
    v, n, i = create_ring(0.155, 0.175, 0.02, 32, center=(bc_x, bc_y + 0.08, bc_z + 0.04))
    mb.append_part('ep_sealing_gasket', 'Driver Sealing O-Ring Gasket', 'concept_sealing_gasket', 'acoustic_tuning', v, n, i)

    # 4. Diaphragm Center Dome (transducer)
    v, n, i = create_dome(0.085, 0.04, 12, 32, center=(bc_x, bc_y + 0.07, bc_z + 0.03))
    mb.append_part('ep_diaphragm_dome', 'Polymer Diaphragm (Center Dome)', 'concept_diaphragm', 'transducer', v, n, i)

    # 5. Diaphragm Corrugated Surround (transducer)
    v, n, i = create_torus(0.115, 0.025, 32, 16, center=(bc_x, bc_y + 0.065, bc_z + 0.03))
    mb.append_part('ep_diaphragm_surround', 'Flexible Diaphragm Roll Surround', 'concept_diaphragm', 'transducer', v, n, i)

    # 6. Precision Copper Voice Coil (transducer)
    v, n, i = create_ring(0.078, 0.086, 0.04, 32, center=(bc_x, bc_y + 0.04, bc_z + 0.03))
    mb.append_part('ep_voice_coil', 'Precision Copper Voice Coil', 'concept_voice_coil', 'transducer', v, n, i)

    # 7. Perforated Driver Basket Frame (transducer)
    v, n, i = create_ring(0.14, 0.17, 0.035, 32, center=(bc_x, bc_y + 0.035, bc_z + 0.025))
    mb.append_part('ep_driver_basket', 'Perforated Driver Basket Frame', 'concept_driver_basket', 'transducer', v, n, i)

    # 8. Rear Damping Acoustic Resistance Cloth (acoustic_tuning)
    v, n, i = create_cylinder(0.138, 0.138, 0.005, 32, center=(bc_x, bc_y + 0.015, bc_z + 0.025), cap_top=True, cap_bottom=True)
    mb.append_part('ep_damping_cloth', 'Rear Damping Acoustic Cloth', 'concept_damping_felt', 'acoustic_tuning', v, n, i)

    # 9. Neodymium (NdFeB) Magnet Ring (magnetic_circuit)
    v, n, i = create_ring(0.035, 0.075, 0.03, 32, center=(bc_x, bc_y + 0.025, bc_z + 0.025))
    mb.append_part('ep_neo_magnet', 'Neodymium (NdFeB) Permanent Magnet', 'concept_magnet_motor', 'magnetic_circuit', v, n, i)

    # 10. Magnetic Steel Pole Piece & Yoke (magnetic_circuit)
    v, n, i = create_cylinder(0.032, 0.078, 0.035, 32, center=(bc_x, bc_y + 0.01, bc_z + 0.025), cap_top=True, cap_bottom=True)
    mb.append_part('ep_pole_piece', 'Magnetic Steel Pole Piece & Yoke', 'concept_magnet_motor', 'magnetic_circuit', v, n, i)

    # 11. Forward Side-Vent Grille (acoustic_tuning)
    v, n, i = create_cylinder(0.035, 0.035, 0.006, 20, center=(bc_x + 0.14, bc_y + 0.09, bc_z + 0.02), cap_top=True, cap_bottom=True)
    mb.append_part('ep_side_vent', 'Forward Side-Vent Grille', 'concept_acoustic_grilles', 'acoustic_tuning', v, n, i)

    # 12. Rear Acoustic Enclosure Shell (enclosure)
    v, n, i = create_lofted_housing(scale=1.0, center=base_center)
    mb.append_part('ep_rear_shell', 'Rear Acoustic Enclosure Shell', 'concept_rear_housing', 'enclosure', v, n, i)

    # 13. Rear Bass Equalization Vent (acoustic_tuning)
    v, n, i = create_box(0.02, 0.06, 0.01, center=(bc_x - 0.16, bc_y + 0.01, bc_z - 0.04))
    mb.append_part('ep_rear_bass_vent', 'Rear Bass Equalization Vent', 'concept_acoustic_grilles', 'acoustic_tuning', v, n, i)

    # 14. Driver Terminal Flex PCB & Solder Pads (electronics)
    v, n, i = create_box(0.08, 0.012, 0.04, center=(bc_x, bc_y - 0.03, bc_z + 0.015))
    mb.append_part('ep_terminal_pcb', 'Driver Terminal Flex PCB & Solder Pads', 'concept_driver_pcb', 'electronics', v, n, i)

    # 15. Oxygen-Free Copper Litz Wire Pair (electronics)
    v, n, i = create_wire_helix(0.005, 0.018, 0.04, 3.5, 16, center=(bc_x, bc_y - 0.22, bc_z - 0.04))
    mb.append_part('ep_litz_wire', 'Oxygen-Free Copper Litz Wire Pair', 'concept_litz_wiring', 'electronics', v, n, i)

    # 16. Lower Stem Housing & Acoustic Duct (enclosure)
    v, n, i = create_cylinder(0.065, 0.055, 0.28, 28, center=(bc_x, bc_y - 0.26, bc_z - 0.045), cap_top=False, cap_bottom=True)
    mb.append_part('ep_stem_casing', 'Lower Stem Housing & Acoustic Duct', 'concept_stem_assembly', 'enclosure', v, n, i)

    # 17. Stem Helmholtz Resonator Bass Vent (acoustic_tuning)
    v, n, i = create_box(0.015, 0.04, 0.02, center=(bc_x, bc_y - 0.38, bc_z - 0.045))
    mb.append_part('ep_stem_bass_vent', 'Stem Helmholtz Resonator Bass Vent', 'concept_acoustic_grilles', 'acoustic_tuning', v, n, i)

    # 18. TPE Stem Strain Relief Boot (controls)
    v, n, i = create_cylinder(0.048, 0.035, 0.08, 24, center=(bc_x, bc_y - 0.44, bc_z - 0.045), cap_top=True, cap_bottom=True)
    mb.append_part('ep_strain_relief', 'TPE Stem Strain Relief Boot', 'concept_cable_interconnect', 'controls', v, n, i)

    # 19. Reinforced Audio Cable Lead (controls)
    v, n, i = create_cylinder(0.028, 0.028, 0.22, 20, center=(bc_x, bc_y - 0.59, bc_z - 0.045), cap_top=True, cap_bottom=True)
    mb.append_part('ep_audio_cable', 'Reinforced Audio Cable Lead', 'concept_cable_interconnect', 'controls', v, n, i)

    # 20. Inline Remote Control Capsule (controls)
    v, n, i = create_box(0.06, 0.18, 0.04, center=(bc_x + 0.22, bc_y - 0.35, bc_z))
    mb.append_part('ep_remote_capsule', 'Inline Remote Control Capsule', 'concept_remote_mic', 'controls', v, n, i)

    # 21. Silicon MEMS Acoustic Sensor & Mic (controls)
    v, n, i = create_box(0.024, 0.032, 0.015, center=(bc_x + 0.22, bc_y - 0.35, bc_z + 0.025))
    mb.append_part('ep_mems_mic', 'Silicon MEMS Acoustic Sensor & Mic', 'concept_remote_mic', 'controls', v, n, i)

    # Concepts grouping:
    concepts = [
        {'id': 'concept_front_housing', 'name': 'Front Nozzle & Acoustic Seal', 'elements': ['ep_front_nozzle']},
        {'id': 'concept_acoustic_grilles', 'name': 'Acoustic Grilles & Bass Vents', 'elements': ['ep_main_grille', 'ep_side_vent', 'ep_rear_bass_vent', 'ep_stem_bass_vent']},
        {'id': 'concept_sealing_gasket', 'name': 'Driver Isolation Gasket', 'elements': ['ep_sealing_gasket']},
        {'id': 'concept_diaphragm', 'name': 'Dynamic Transducer Diaphragm', 'elements': ['ep_diaphragm_dome', 'ep_diaphragm_surround']},
        {'id': 'concept_voice_coil', 'name': 'Micro-Wound Copper Voice Coil', 'elements': ['ep_voice_coil']},
        {'id': 'concept_driver_basket', 'name': 'Acoustic Driver Frame & Chassis', 'elements': ['ep_driver_basket']},
        {'id': 'concept_damping_felt', 'name': 'Acoustic Resistance Damping Felt', 'elements': ['ep_damping_cloth']},
        {'id': 'concept_magnet_motor', 'name': 'Neodymium Magnet Motor Circuit', 'elements': ['ep_neo_magnet', 'ep_pole_piece']},
        {'id': 'concept_rear_housing', 'name': 'Rear Acoustic Shell Enclosure', 'elements': ['ep_rear_shell']},
        {'id': 'concept_driver_pcb', 'name': 'Flex PCB Solder Terminal', 'elements': ['ep_terminal_pcb']},
        {'id': 'concept_litz_wiring', 'name': 'Internal Litz Wire Harness', 'elements': ['ep_litz_wire']},
        {'id': 'concept_stem_assembly', 'name': 'Stem Resonator Housing', 'elements': ['ep_stem_casing']},
        {'id': 'concept_cable_interconnect', 'name': 'Cable Lead & Strain Relief Boot', 'elements': ['ep_strain_relief', 'ep_audio_cable']},
        {'id': 'concept_remote_mic', 'name': 'Inline Remote & MEMS Microphone', 'elements': ['ep_remote_capsule', 'ep_mems_mic']},
    ]

    explanations = {
        'front nozzle & acoustic seal': 'Directs acoustic pressure waves straight toward the ear canal. Shaped through 3D ear scans to sit snugly in the concha with minimal sound leakage.',
        'acoustic grilles & bass vents': 'Laser-perforated acoustic micro-grilles. Crucially, the rear and stem vents equalize chamber pressure, tuning Helmholtz resonance so you get punchy, deep bass without an airtight silicone ear tip.',
        'driver isolation gasket': 'An airtight elastomer ring isolating the driver front and rear acoustic chambers. Eliminates acoustic phase cancellation between opposing wave fronts.',
        'dynamic transducer diaphragm': 'A multi-layer polymer membrane. The rigid center dome reproduces crisp high frequencies up to 20 kHz, while the flexible outer roll surround provides high excursion for deep low-end response.',
        'micro-wound copper voice coil': 'A delicate coil of insulated copper wire bonded to the diaphragm. Interacts with the magnetic gap to convert electrical music pulses into physical vibrations.',
        'acoustic driver frame & chassis': 'The rigid metal backbone holding the motor and diaphragm in sub-millimeter concentric alignment, featuring rear acoustic venting windows.',
        'acoustic resistance damping felt': 'Calibrated porous mesh placed over rear driver windows. Provides acoustic resistance to damp sharp midrange resonant peaks for a neutral frequency curve.',
        'neodymium magnet motor circuit': 'Sintered NdFeB rare-earth permanent magnet paired with a high-permeability steel pole yoke. Concentrates an intense magnetic field across the air gap for lightning-fast transient response.',
        'rear acoustic shell enclosure': 'The smooth white outer shell forming the back cavity. Its internal volume is tuned to prevent air stiffness from inhibiting bass movement.',
        'flex pcb solder terminal': 'Polyimide flexible substrate with micro gold pads connecting the hair-thin moving voice coil wires to the incoming main cable leads.',
        'internal litz wire harness': 'Braided enamel-coated oxygen-free copper strands. Offers zero skin-effect resistance, ultra-low impedance, and extreme fatigue resistance.',
        'stem resonator housing': 'The counterweighted lower stem. Acts as an internal bass reflex waveguide that pipes lower audio frequencies down to the bottom exhaust port.',
        'cable lead & strain relief boot': 'TPE jacketed cable reinforced with internal high-tensile Kevlar aramid fibers to withstand heavy tugs, combined with a tapered strain relief boot to avoid wire pinching.',
        'inline remote & mems microphone': 'Silicone MEMS acoustic sensor chip with micro-etched diaphragm and internal ADC pre-amp, delivering high SNR speech clarity for calls and Siri.',
    }

    bin_path = out_dir / 'earpods-0.bin'
    bin_path.write_bytes(mb.blob)
    print(f"Wrote {len(mb.blob)} bytes to {bin_path}")

    manifest = {
        'version': 'Apple EarPods Deconstructed 1.0',
        'itemName': 'Apple EarPods',
        'subtitle': 'Acoustic Engineering & Hardware Architecture',
        'parts': mb.parts,
        'concepts': concepts,
        'systems': systems,
        'explanations': explanations,
        'chunks': [{
            'url': '/models/earpods-0.bin',
            'bytes': len(mb.blob)
        }],
        'triangles': mb.total_triangles
    }

    json_path = out_dir / 'earpods.json'
    json_path.write_text(json.dumps(manifest, separators=(',', ':')))
    print(f"Wrote manifest to {json_path} ({len(mb.parts)} parts, {len(concepts)} concepts, {mb.total_triangles} triangles)")

if __name__ == '__main__':
    main()
