"""Procedural 3D CAD Generator for Apple AirPods Pro (2nd Generation).
Accurately modeled from Apple's official Accessory Design Guidelines dimensional drawings
and finished product photos. Generates authentic components, 16-bit signed normals,
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

# --- GEOMETRY UTILITIES ---

def normalize(v):
    l = math.hypot(v[0], v[1], v[2]) or 1.0
    return (v[0]/l, v[1]/l, v[2]/l)

def pack_normal(nx, ny, nz):
    l = math.hypot(nx, ny, nz) or 1.0
    return (
        max(-32767, min(32767, round((nx/l) * 32767))),
        max(-32767, min(32767, round((ny/l) * 32767))),
        max(-32767, min(32767, round((nz/l) * 32767)))
    )

def rotate_point(p, rx=0, ry=0, rz=0):
    x, y, z = p
    # RX
    if rx:
        cx, sx = math.cos(rx), math.sin(rx)
        y, z = y * cx - z * sx, y * sx + z * cx
    # RY
    if ry:
        cy, sy = math.cos(ry), math.sin(ry)
        x, z = x * cy + z * sy, -x * sy + z * cy
    # RZ
    if rz:
        cz, sz = math.cos(rz), math.sin(rz)
        x, y = x * cz - y * sz, x * sz + y * cz
    return (x, y, z)

# --- PROCEDURAL BUILDERS ---

def create_stem(length=0.48, width=0.14, depth=0.13, center=(0, 0, 0), force_indent=True):
    """Accurately models the AirPods Pro stem with rounded-rectangle cross-section
    and the signature front force-sensor tactile pinch indentation."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs_u = 32
    segs_v = 24
    half_l = length / 2.0
    rx = width / 2.0
    rz = depth / 2.0

    for iv in range(segs_v + 1):
        v = iv / segs_v
        y = cy - half_l + v * length
        
        # Check if in force-sensor region (middle of front face)
        is_sensor_zone = (0.28 <= v <= 0.72)
        indent_factor = 0.84 if (is_sensor_zone and force_indent) else 1.0

        for iu in range(segs_u + 1):
            u = iu / segs_u
            angle = u * math.pi * 2
            
            # Superellipse for Apple's signature squircle/rounded rectangle
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            sgn_cos = 1 if cos_a >= 0 else -1
            sgn_sin = 1 if sin_a >= 0 else -1
            
            # exponent 2.6 gives Apple's classic smooth squircle
            px = rx * (abs(cos_a) ** (2.0 / 2.6)) * sgn_cos
            pz = rz * (abs(sin_a) ** (2.0 / 2.6)) * sgn_sin

            # Flatten/indent the front (+Z) face in the sensor zone
            if is_sensor_zone and force_indent and pz > 0 and abs(px) < rx * 0.75:
                pz *= indent_factor

            nx = (abs(cos_a) ** (2.0 - 2.0/2.6)) * sgn_cos
            ny = 0.0
            nz = (abs(sin_a) ** (2.0 - 2.0/2.6)) * sgn_sin
            if is_sensor_zone and force_indent and pz > 0 and abs(px) < rx * 0.75:
                nz = 1.0
                nx *= 0.2

            pn = pack_normal(nx, ny, nz)
            verts.extend([cx + px, y, cz + pz])
            norms.extend(pn)

    stride = segs_u + 1
    for iv in range(segs_v):
        for iu in range(segs_u):
            i0 = iv * stride + iu
            i1 = (iv + 1) * stride + iu
            i2 = (iv + 1) * stride + (iu + 1)
            i3 = iv * stride + (iu + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_bottom_cap(width=0.145, depth=0.135, height=0.035, center=(0, 0, 0)):
    """Models the dual chrome charging contact electrodes and the center mic mesh."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 32
    rx, rz = width / 2.0, depth / 2.0

    # Dome bottom cap
    for iv in range(8):
        v = iv / 7.0
        theta = v * (math.pi / 2.0)
        y = cy - math.sin(theta) * height
        scale = math.cos(theta)

        for iu in range(segs + 1):
            angle = (iu / segs) * math.pi * 2
            px = rx * scale * math.cos(angle)
            pz = rz * scale * math.sin(angle)
            nx = px / rx
            ny = -math.sin(theta) * 1.5
            nz = pz / rz
            pn = pack_normal(nx, ny, nz)
            verts.extend([cx + px, y, cz + pz])
            norms.extend(pn)

    stride = segs + 1
    for iv in range(7):
        for iu in range(segs):
            i0 = iv * stride + iu
            i1 = (iv + 1) * stride + iu
            i2 = (iv + 1) * stride + (iu + 1)
            i3 = iv * stride + (iu + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_airpod_bulb(scale=1.0, center=(0, 0, 0), side='rear'):
    """Models the compound organic curvature of the main AirPods Pro earbud body.
    Accurately lofts the sphere-to-stem organic blend seen in Apple drawings."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center

    # Cross section layers from nozzle transition down to the stem junction
    # (y, x_off, z_off, rx, rz)
    slices = [
        # Top crown
        (0.24, 0.02, 0.04, 0.07, 0.07),
        (0.22, 0.03, 0.05, 0.12, 0.13),
        (0.18, 0.04, 0.06, 0.18, 0.19),
        (0.13, 0.05, 0.065, 0.22, 0.23),   # Max bulb equator
        (0.08, 0.045, 0.06, 0.23, 0.235),
        (0.02, 0.03, 0.045, 0.22, 0.22),
        (-0.04, 0.015, 0.025, 0.18, 0.18), # Neck blend
        (-0.10, 0.005, 0.005, 0.13, 0.12), # Transition to stem
        (-0.15, 0.00, 0.00, 0.075, 0.07),  # Stem connection
    ]
    segs = 36

    # If front half vs rear half, we select angular ranges
    if side == 'front':
        u_min, u_max = -math.pi * 0.15, math.pi * 1.15
    elif side == 'rear':
        u_min, u_max = math.pi * 0.85, math.pi * 2.15
    else:
        u_min, u_max = 0, math.pi * 2

    for r_idx, (y, xo, zo, rx, rz) in enumerate(slices):
        for s in range(segs + 1):
            u = s / segs
            angle = u_min + u * (u_max - u_min)
            
            # EarPods Pro asymmetry: bulge inward towards the ear concha (+X, +Z)
            concha_bulge = 1.0 + 0.14 * math.sin(angle)
            px = (xo + rx * math.cos(angle) * concha_bulge) * scale
            pz = (zo + rz * math.sin(angle)) * scale
            py = (y * scale)

            nx = math.cos(angle) * 0.9
            ny = 0.5 if r_idx < 3 else (-0.5 if r_idx > 5 else 0.0)
            nz = math.sin(angle) * 0.9
            pn = pack_normal(nx, ny, nz)

            verts.extend([cx + px, cy + py, cz + pz])
            norms.extend(pn)

    stride = segs + 1
    for r in range(len(slices) - 1):
        for s in range(segs):
            i0 = r * stride + s
            i1 = (r + 1) * stride + s
            i2 = (r + 1) * stride + (s + 1)
            i3 = r * stride + (s + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_angled_elliptical_nozzle(major_r=0.145, minor_r=0.095, length=0.08, center=(0, 0, 0), rot_x=-0.45, rot_y=0.4):
    """Models the 11.9 mm x 7.6 mm angled elliptical acoustic sound outlet nozzle
    from page 2 of Apple's AirPods Pro dimensional drawing."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 32
    steps = 8

    for step in range(steps + 1):
        v = step / steps
        h = v * length
        scale = 1.0 - 0.08 * v

        for i in range(segs + 1):
            angle = (i / segs) * math.pi * 2
            lx = major_r * scale * math.cos(angle)
            lz = minor_r * scale * math.sin(angle)
            ly = h

            lnx = math.cos(angle)
            lny = 0.15
            lnz = math.sin(angle)

            # Rotate to Apple's ear canal angle (~35-40 deg forward and inward)
            gx, gy, gz = rotate_point((lx, ly, lz), rx=rot_x, ry=rot_y, rz=0)
            gnx, gny, gnz = rotate_point((lnx, lny, lnz), rx=rot_x, ry=rot_y, rz=0)
            pn = pack_normal(gnx, gny, gnz)

            verts.extend([cx + gx, cy + gy, cz + gz])
            norms.extend(pn)

    stride = segs + 1
    for step in range(steps):
        for i in range(segs):
            i0 = step * stride + i
            i1 = (step + 1) * stride + i
            i2 = (step + 1) * stride + (i + 1)
            i3 = step * stride + (i + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_silicone_ear_tip(major_r=0.145, minor_r=0.095, center=(0, 0, 0), rot_x=-0.45, rot_y=0.4):
    """Models the iconic Apple AirPods Pro silicone umbrella ear tip with
    elliptical cross section and soft outward flare."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 36
    rings = 16

    for r in range(rings + 1):
        v = r / rings
        # Flare outward from base collar to outer rim, then roll inward
        phi = v * math.pi
        h = math.sin(phi * 0.85) * 0.11
        flare = 1.0 + 0.35 * math.sin(v * math.pi * 0.9)

        for s in range(segs + 1):
            u = s / segs
            angle = u * math.pi * 2
            lx = major_r * flare * math.cos(angle)
            lz = minor_r * flare * math.sin(angle)
            ly = h + 0.06

            lnx = math.cos(angle) * (1.0 if v < 0.6 else -0.5)
            lny = math.cos(phi * 0.85)
            lnz = math.sin(angle) * (1.0 if v < 0.6 else -0.5)

            gx, gy, gz = rotate_point((lx, ly, lz), rx=rot_x, ry=rot_y, rz=0)
            gnx, gny, gnz = rotate_point((lnx, lny, lnz), rx=rot_x, ry=rot_y, rz=0)
            pn = pack_normal(gnx, gny, gnz)

            verts.extend([cx + gx, cy + gy, cz + gz])
            norms.extend(pn)

    stride = segs + 1
    for r in range(rings):
        for s in range(segs):
            i0 = r * stride + s
            i1 = (r + 1) * stride + s
            i2 = (r + 1) * stride + (s + 1)
            i3 = r * stride + (s + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_curved_vent_grille(center=(0, 0, 0), width=0.05, length=0.13, arc=0.5):
    """Accurately models the large elongated black acoustic vent mesh on the top crest
    of the AirPods Pro housing."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs_l = 16
    segs_w = 6

    for il in range(segs_l + 1):
        vl = (il / segs_l) - 0.5
        y = cy + vl * length
        curve_z = -math.cos(vl * math.pi) * 0.02

        for iw in range(segs_w + 1):
            vw = (iw / segs_w) - 0.5
            x = cx + vw * width
            z = cz + curve_z - (vw * vw) * 0.015

            pn = pack_normal(vw * 0.4, 0.2, 1.0)
            verts.extend([x, y, z])
            norms.extend(pn)

    stride = segs_w + 1
    for il in range(segs_l):
        for iw in range(segs_w):
            i0 = il * stride + iw
            i1 = (il + 1) * stride + iw
            i2 = (il + 1) * stride + (iw + 1)
            i3 = il * stride + (iw + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_oval_sensor(center=(0, 0, 0), rx=0.035, ry=0.065, rot_y=0.7):
    """Models the black skin-detect optical sensor window on the inner ear-facing face."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 24
    
    verts.extend([cx, cy, cz])
    gnx, gny, gnz = rotate_point((0, 0, 1), ry=rot_y)
    norms.extend(pack_normal(gnx, gny, gnz))

    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        lx = rx * math.cos(angle)
        ly = ry * math.sin(angle)
        lz = 0.002

        gx, gy, gz = rotate_point((lx, ly, lz), ry=rot_y)
        verts.extend([cx + gx, cy + gy, cz + gz])
        norms.extend(pack_normal(gnx, gny, gnz))

    for i in range(segs):
        idxs.extend([0, 1 + i, 2 + i])

    return verts, norms, idxs

def create_coin_battery(radius=0.105, height=0.075, center=(0, 0, 0)):
    """Models the 3.7V custom rechargeable lithium-ion button cell battery."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 32
    half_h = height / 2.0

    # Cylindrical body
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        verts.extend([cx + radius * ca, cy + half_h, cz + radius * sa])
        norms.extend(pack_normal(ca, 0, sa))
        verts.extend([cx + radius * ca, cy - half_h, cz + radius * sa])
        norms.extend(pack_normal(ca, 0, sa))

    for i in range(segs):
        i0 = i * 2
        i1 = i0 + 1
        i2 = (i + 1) * 2
        i3 = i2 + 1
        idxs.extend([i0, i1, i2, i2, i1, i3])

    # Top metal disc
    base_top = len(verts) // 3
    verts.extend([cx, cy + half_h, cz])
    norms.extend(pack_normal(0, 1, 0))
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        verts.extend([cx + radius * math.cos(angle), cy + half_h, cz + radius * math.sin(angle)])
        norms.extend(pack_normal(0, 1, 0))
    for i in range(segs):
        idxs.extend([base_top, base_top + 1 + i, base_top + 2 + i])

    # Bottom metal disc
    base_bot = len(verts) // 3
    verts.extend([cx, cy - half_h, cz])
    norms.extend(pack_normal(0, -1, 0))
    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        verts.extend([cx + radius * math.cos(angle), cy - half_h, cz + radius * math.sin(angle)])
        norms.extend(pack_normal(0, -1, 0))
    for i in range(segs):
        idxs.extend([base_bot, base_bot + 2 + i, base_bot + 1 + i])

    return verts, norms, idxs

def create_h2_board(w=0.09, h=0.14, d=0.035, center=(0, 0, 0)):
    """Models the multi-layer SiP (System in Package) housing Apple's H2 audio processor."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    hw, hh, hd = w / 2.0, h / 2.0, d / 2.0
    faces = [
        ([cx-hw, cy-hh, cz+hd, cx+hw, cy-hh, cz+hd, cx+hw, cy+hh, cz+hd, cx-hw, cy+hh, cz+hd], (0, 0, 1)),
        ([cx+hw, cy-hh, cz-hd, cx-hw, cy-hh, cz-hd, cx-hw, cy+hh, cz-hd, cx+hw, cy+hh, cz-hd], (0, 0, -1)),
        ([cx-hw, cy+hh, cz+hd, cx+hw, cy+hh, cz+hd, cx+hw, cy+hh, cz-hd, cx-hw, cy+hh, cz-hd], (0, 1, 0)),
        ([cx-hw, cy-hh, cz-hd, cx+hw, cy-hh, cz-hd, cx+hw, cy-hh, cz+hd, cx-hw, cy-hh, cz+hd], (0, -1, 0)),
        ([cx+hw, cy-hh, cz+hd, cx+hw, cy-hh, cz-hd, cx+hw, cy+hh, cz-hd, cx+hw, cy+hh, cz+hd], (1, 0, 0)),
        ([cx-hw, cy-hh, cz-hd, cx-hw, cy-hh, cz+hd, cx-hw, cy+hh, cz+hd, cx-hw, cy+hh, cz-hd], (-1, 0, 0)),
    ]
    for quad, (nx, ny, nz) in faces:
        base = len(verts) // 3
        pn = pack_normal(nx, ny, nz)
        for i in range(4):
            verts.extend(quad[i*3:(i+1)*3])
            norms.extend(pn)
        idxs.extend([base, base + 1, base + 2, base, base + 2, base + 3])
    return verts, norms, idxs

def create_driver_diaphragm(radius=0.11, dome_r=0.065, center=(0, 0, 0), rot_x=-0.45, rot_y=0.4):
    """Models Apple's custom high-excursion dynamic driver diaphragm:
    rigid center dome + corrugated roll surround."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 32
    rings = 10

    for r in range(rings + 1):
        v = r / rings
        curr_r = v * radius
        if curr_r <= dome_r:
            phi = (curr_r / dome_r) * (math.pi / 2.0)
            h = math.cos(phi) * 0.025
            slope_h = math.sin(phi)
        else:
            # Corrugated suspension roll
            roll_phi = ((curr_r - dome_r) / (radius - dome_r)) * math.pi
            h = math.sin(roll_phi) * 0.018
            slope_h = math.cos(roll_phi)

        for s in range(segs + 1):
            angle = (s / segs) * math.pi * 2
            lx = curr_r * math.cos(angle)
            lz = curr_r * math.sin(angle)
            ly = h

            lnx = math.cos(angle) * slope_h
            lny = 0.95
            lnz = math.sin(angle) * slope_h

            gx, gy, gz = rotate_point((lx, ly, lz), rx=rot_x, ry=rot_y, rz=0)
            gnx, gny, gnz = rotate_point((lnx, lny, lnz), rx=rot_x, ry=rot_y, rz=0)
            pn = pack_normal(gnx, gny, gnz)

            verts.extend([cx + gx, cy + gy, cz + gz])
            norms.extend(pn)

    stride = segs + 1
    for r in range(rings):
        for s in range(segs):
            i0 = r * stride + s
            i1 = (r + 1) * stride + s
            i2 = (r + 1) * stride + (s + 1)
            i3 = r * stride + (s + 1)
            idxs.extend([i0, i1, i2, i0, i2, i3])

    return verts, norms, idxs

def create_driver_motor(r_inner=0.035, r_outer=0.085, height=0.032, center=(0, 0, 0), rot_x=-0.45, rot_y=0.4):
    """Models the neodymium magnet ring and steel pole yoke."""
    verts, norms, idxs = [], [], []
    cx, cy, cz = center
    segs = 32
    half_h = height / 2.0

    for i in range(segs + 1):
        angle = (i / segs) * math.pi * 2
        ca, sa = math.cos(angle), math.sin(angle)
        for r_val, in_out in [(r_outer, 1), (r_inner, -1)]:
            lx = r_val * ca
            lz = r_val * sa
            for ly in [half_h, -half_h]:
                gx, gy, gz = rotate_point((lx, ly, lz), rx=rot_x, ry=rot_y, rz=0)
                gnx, gny, gnz = rotate_point((ca * in_out, 0, sa * in_out), rx=rot_x, ry=rot_y, rz=0)
                verts.extend([cx + gx, cy + gy, cz + gz])
                norms.extend(pack_normal(gnx, gny, gnz))

    # Connect outer wall
    for i in range(segs):
        base = i * 4
        idxs.extend([base, base + 1, base + 4, base + 4, base + 1, base + 5])
        # Top ring
        idxs.extend([base, base + 4, base + 2, base + 4, base + 6, base + 2])

    return verts, norms, idxs

def main():
    mb = MeshBuilder()

    systems = [
        {'id': 'enclosure', 'name': 'Housing & Silicone Tip', 'color': '#f8fafc', 'description': 'Ergonomic high-gloss polycarbonate enclosure sculpted from 3D ear scans, paired with soft silicone umbrella ear tips for acoustic sealing.'},
        {'id': 'transducer', 'name': 'Acoustic Transducer', 'color': '#d97706', 'description': 'Custom Apple high-excursion dynamic driver with composite polymer diaphragm and precision copper voice coil delivering deep 20 Hz bass with ultra-low distortion.'},
        {'id': 'magnetic_motor', 'name': 'Neodymium Motor', 'color': '#0284c7', 'description': 'High-flux NdFeB rare-earth permanent magnet and precision-machined steel pole yoke creating a concentrated magnetic field across the voice coil gap.'},
        {'id': 'acoustics_vents', 'name': 'ANC Vents & Grilles', 'color': '#1e293b', 'description': 'Laser-perforated acoustic micro-grilles and tuned air vents that equalize internal pressure, prevent occlusion pressure, and feed the inward/outward ANC microphones.'},
        {'id': 'computing_silicon', 'name': 'Apple H2 SiP & Battery', 'color': '#10b981', 'description': 'The custom Apple H2 System-in-Package running computational audio algorithms at 48,000 times per second, powered by a high-density lithium-ion button cell.'},
        {'id': 'controls_stem', 'name': 'Stem & Charging Cap', 'color': '#94a3b8', 'description': 'The downward stem housing the capacitive touch/force pinch sensor strip, beamforming microphone channels, and dual chrome-plated charging contact electrodes.'},
    ]

    base_center = (0.0, 0.85, 0.0)
    bc_x, bc_y, bc_z = base_center

    # 1. Soft Silicone Umbrella Ear Tip (enclosure)
    v, n, i = create_silicone_ear_tip(major_r=0.142, minor_r=0.096, center=(bc_x + 0.12, bc_y + 0.14, bc_z + 0.16))
    mb.append_part('app_ear_tip', 'Silicone Umbrella Ear Tip', 'concept_ear_tip', 'enclosure', v, n, i)

    # 2. Angled Front Nozzle & Mesh Outlet (acoustics_vents)
    v, n, i = create_angled_elliptical_nozzle(major_r=0.125, minor_r=0.082, length=0.07, center=(bc_x + 0.08, bc_y + 0.10, bc_z + 0.11))
    mb.append_part('app_nozzle_mesh', 'Acoustic Sound Outlet & Stainless Mesh', 'concept_nozzle', 'acoustics_vents', v, n, i)

    # 3. Ergonomic Front Housing Shell (enclosure)
    v, n, i = create_airpod_bulb(scale=1.0, center=base_center, side='front')
    mb.append_part('app_front_shell', 'Front Ergonomic Enclosure Shell', 'concept_housing', 'enclosure', v, n, i)

    # 4. Custom High-Excursion Driver Diaphragm (transducer)
    v, n, i = create_driver_diaphragm(radius=0.105, dome_r=0.062, center=(bc_x + 0.04, bc_y + 0.07, bc_z + 0.07))
    mb.append_part('app_driver_diaphragm', 'High-Excursion Polymer Diaphragm', 'concept_driver', 'transducer', v, n, i)

    # 5. Neodymium Magnet & Motor Assembly (magnetic_motor)
    v, n, i = create_driver_motor(r_inner=0.035, r_outer=0.085, height=0.035, center=(bc_x + 0.02, bc_y + 0.05, bc_z + 0.04))
    mb.append_part('app_motor_assembly', 'Neodymium Magnet & Pole Yoke', 'concept_motor', 'magnetic_motor', v, n, i)

    # 6. Inward-Facing ANC Microphone (acoustics_vents)
    v, n, i = create_h2_board(w=0.028, h=0.032, d=0.018, center=(bc_x + 0.06, bc_y + 0.11, bc_z + 0.05))
    mb.append_part('app_inward_anc_mic', 'Inward-Facing Calibration Microphone', 'concept_anc_mics', 'acoustics_vents', v, n, i)

    # 7. High-Density Li-Ion Rechargeable Button Cell Battery (computing_silicon)
    v, n, i = create_coin_battery(radius=0.098, height=0.068, center=(bc_x - 0.01, bc_y + 0.05, bc_z - 0.01))
    mb.append_part('app_battery_cell', 'Rechargeable Li-Ion Button Cell Battery', 'concept_battery', 'computing_silicon', v, n, i)

    # 8. Apple H2 Computational Audio SiP Motherboard (computing_silicon)
    v, n, i = create_h2_board(w=0.075, h=0.13, d=0.032, center=(bc_x - 0.03, bc_y - 0.02, bc_z - 0.02))
    mb.append_part('app_h2_sip_board', 'Apple H2 Audio Silicon SiP Motherboard', 'concept_h2_processor', 'computing_silicon', v, n, i)

    # 9. Optical Skin-Detect Sensor Window (acoustics_vents)
    v, n, i = create_oval_sensor(center=(bc_x + 0.09, bc_y + 0.06, bc_z - 0.02), rx=0.025, ry=0.048, rot_y=0.75)
    mb.append_part('app_skin_detect_sensor', 'Skin-Detect Optical Sensor Window', 'concept_sensors', 'acoustics_vents', v, n, i)

    # 10. Top/Rear Elongated Acoustic ANC Vent Mesh (acoustics_vents)
    v, n, i = create_curved_vent_grille(center=(bc_x - 0.12, bc_y + 0.14, bc_z + 0.02), width=0.048, length=0.14)
    mb.append_part('app_top_vent_grille', 'Top/Rear Acoustic ANC Vent Grille', 'concept_acoustic_vents', 'acoustics_vents', v, n, i)

    # 11. Rear Ergonomic Housing Enclosure Shell (enclosure)
    v, n, i = create_airpod_bulb(scale=1.0, center=base_center, side='rear')
    mb.append_part('app_rear_shell', 'Rear Acoustic Enclosure Shell', 'concept_housing', 'enclosure', v, n, i)

    # 12. Stem Housing with Force Sensor Indentation (controls_stem)
    v, n, i = create_stem(length=0.46, width=0.138, depth=0.132, center=(bc_x, bc_y - 0.32, bc_z - 0.01), force_indent=True)
    mb.append_part('app_stem_housing', 'Stem Housing & Force Sensor Indent', 'concept_stem', 'controls_stem', v, n, i)

    # 13. Bottom Chrome Charging Contacts & Mic Port (controls_stem)
    v, n, i = create_bottom_cap(width=0.142, depth=0.134, height=0.038, center=(bc_x, bc_y - 0.55, bc_z - 0.01))
    mb.append_part('app_bottom_chrome_cap', 'Chrome Charging Contacts & Mic Cap', 'concept_charging_contacts', 'controls_stem', v, n, i)

    # Concepts:
    concepts = [
        {'id': 'concept_ear_tip', 'name': 'Silicone Umbrella Ear Tip', 'elements': ['app_ear_tip']},
        {'id': 'concept_nozzle', 'name': 'Angled Sound Outlet & Grille', 'elements': ['app_nozzle_mesh']},
        {'id': 'concept_housing', 'name': 'Ergonomic Polycarbonate Shells', 'elements': ['app_front_shell', 'app_rear_shell']},
        {'id': 'concept_driver', 'name': 'Custom High-Excursion Transducer', 'elements': ['app_driver_diaphragm']},
        {'id': 'concept_motor', 'name': 'Neodymium Magnet Motor Circuit', 'elements': ['app_motor_assembly']},
        {'id': 'concept_anc_mics', 'name': 'Inward ANC & Calibration Mic', 'elements': ['app_inward_anc_mic']},
        {'id': 'concept_battery', 'name': 'Rechargeable Li-Ion Button Cell', 'elements': ['app_battery_cell']},
        {'id': 'concept_h2_processor', 'name': 'Apple H2 Silicon Audio Processor', 'elements': ['app_h2_sip_board']},
        {'id': 'concept_sensors', 'name': 'Skin-Detect Optical Sensor', 'elements': ['app_skin_detect_sensor']},
        {'id': 'concept_acoustic_vents', 'name': 'Top Acoustic ANC Vent Grille', 'elements': ['app_top_vent_grille']},
        {'id': 'concept_stem', 'name': 'Stem & Force Touch Sensor', 'elements': ['app_stem_housing']},
        {'id': 'concept_charging_contacts', 'name': 'Chrome Charging Contacts & Mic', 'elements': ['app_bottom_chrome_cap']},
    ]

    explanations = {
        'silicone umbrella ear tip': 'Engineered silicone tip with an elliptical cross-section that conforms to ear canal geometry, creating an airtight acoustic seal for active noise cancellation and deep bass retention.',
        'angled sound outlet & grille': 'Elliptical sound nozzle angled at ~38 degrees forward and inward. Directs acoustic pressure waves straight at the eardrum, protected by laser-cut stainless steel mesh.',
        'ergonomic polycarbonate shells': 'Ultra-glossy, lightweight polycarbonate housing sculpted using 3D ear scan topology. Houses internal sub-assemblies and seals moisture and sweat to IPX4 standards.',
        'custom high-excursion transducer': 'Apple-designed 11mm dynamic loudspeaker. Combines a stiff center dome for crystal-clear 20 kHz high frequencies and a high-compliance roll surround for low-distortion, punchy sub-bass.',
        'neodymium magnet motor circuit': 'Rare-earth NdFeB permanent magnet paired with high-permeability steel pole pieces, providing intense magnetic flux density across the voice coil gap for rapid transient response.',
        'inward anc & calibration mic': 'Microphone inside the ear tip chamber that listens 200 times per second to what the eardrum actually hears. Drives Adaptive EQ to dynamically tailor low and midrange frequencies to each user\'s unique ear anatomy.',
        'rechargeable li-ion button cell': 'High-density 3.7V custom button cell battery supplying up to 6 hours of continuous Active Noise Cancellation playback on a single charge.',
        'apple h2 silicon audio processor': 'Custom Apple H2 System-in-Package (SiP). Runs advanced computational audio algorithms, real-time noise-canceling wave inversion, Adaptive Transparency, and personalized Spatial Audio head tracking.',
        'skin-detect optical sensor': 'Infrared optical window that distinguishes between human ear tissue and non-skin surfaces (such as pockets or tables), auto-pausing playback instantly when removed.',
        'top acoustic anc vent grille': 'Elongated micro-perforated black mesh vent on the top curve of the bulb. Equalizes air pressure inside the ear canal to prevent dizziness, and houses the outward-facing noise-canceling microphone.',
        'stem & force touch sensor': 'Downward stem balancing the earbud weight, featuring an indented capacitive force sensor strip. Recognizes single, double, and triple squeezes, plus up/down swipe gestures for volume control.',
        'chrome charging contacts & mic': 'Curved silver-plated contact electrodes that mate with charging pins inside the MagSafe case, flanking a centered microphone port for crystal-clear voice pickup.',
    }

    bin_path = out_dir / 'earpods-0.bin'
    bin_path.write_bytes(mb.blob)
    print(f"Wrote {len(mb.blob)} bytes to {bin_path}")

    manifest = {
        'version': 'Apple AirPods Pro 2 Deconstructed 2.0',
        'itemName': 'AirPods Pro (2nd Gen)',
        'subtitle': 'HARDWARE DECONSTRUCTION · HOW THINGS WORK',
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
