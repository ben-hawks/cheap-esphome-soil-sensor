"""
Outdoor soil-sensor enclosure: XIAO ESP32-C6 + wrapped 18650 pack (69 x 22.2 x 18.6) +
Capacitive Soil Moisture Sensor v2.0 (22 x 100 mm PCB).

The probe passes through a slot in the floor. The sensor's electronics head
stays inside the box. A slide-in fork engages the two side grooves on the
sensor PCB and screws to two pillars, so the probe can't be pulled out or
pushed in further. The floor's underside sits 13 mm below the probe's warning
line, inside the maker's recommended band, so the box rests on the soil. Two printed blade stakes drop through
sockets on the left and right walls to stop it rocking.

Outputs (STL, mm):
  box.stl          print floor-down, no supports
  lid.stl          already flipped (top face on the bed), no supports
  sensor_fork.stl  print flat
  gasket_tpu.stl   optional, TPU, sits in the lid groove
  stake.stl        print 2, flat

A DS18B20 waterproof probe (6 x 50 mm tube) is buried whole beside the moisture probe;
its cable enters through a PG7 gland screwed into a threaded boss in the floor.

Requires: pip install manifold3d trimesh numpy
Edit the PARAMETERS block and re-run: python3 soil_enclosure.py [output_dir]
(writes to ./stl next to this script by default)
"""
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection

# ---------------- PARAMETERS ----------------
SEG = 64

WALL = 2.4            # 6 perimeters at 0.4 nozzle
FLOOR = 3.0
IX, IY, IZ = 90.0, 58.0, 56.0   # interior size (X width, Y depth, Z height)
OUT_R = 4.0           # outer corner radius

# Battery: ELXJAR wrapped 18650 pack with leads, 69 mm long, ~19 mm cell. Bay along the
# front wall; two snap cradles hold it (press it down through the opening, leads on top).
BATT_LEN, BATT_W = 72.0, 25.0   # bay length (X) / width (Y)
BATT_Y0 = 3.0                   # gap from the front interior wall (room for a zip tie)
CELL_D = 19.0                   # measured cell diameter
CRADLE_CLEAR = 0.2              # radial clearance in the cradle
CRADLE_WALL = 2.2               # cradle ring thickness
CRADLE_OPEN = 17.6              # snap opening; ~1.4 mm narrower than the cell
CRADLE_T = 6.0                  # cradle thickness along the cell
CRADLE_X = 26.0                 # cradles at centre +/- this

# Sensor PCB
PCB_W, PCB_T = 22.0, 1.6
SLOT_W, SLOT_T = 22.6, 2.0      # floor slot (seal it with silicone after fitting)
SENSOR_Y = 40.0                 # interior Y of the PCB plane
GROOVE_DEPTH = 1.2              # how far each side groove cuts into the PCB edge
# Probe depth, measured from the top edge of the sensor PCB (from the product diagram):
GROOVE_FROM_TOP = 19.8          # side grooves
SOIL_FROM_TOP = 44.0            # floor underside = soil surface; recommended band ~41-64,
                                # red warning line ~31 (never bury past it)
GROOVE_Z = SOIL_FROM_TOP - FLOOR - GROOVE_FROM_TOP   # groove centre above floor's top face
FORK_T = 1.8                    # fork plate thickness (groove is ~2.2 tall)
PILLAR = 8.0

# XIAO ESP32-C6 in a card guide: two slotted rails grip its long edges; USB-C up,
# top side (wires) faces the open interior, flat underside (divider / pull-up) the wall
XIAO_BOARD_W = 17.8             # board width (edge to edge)
XIAO_PCB_T = 1.0                # measure yours; slot = this + XIAO_SLOT_CLEAR
XIAO_SLOT_CLEAR = 0.3
XIAO_GRIP = 1.0                 # how far the rails overlap each board face
XIAO_RAIL_H = 8.0               # covers only the unused bottom pin rows (D4-D6 / D7-D9)
XIAO_WALL_GAP = 13.0            # board plane to right interior wall (underside parts + fingers)
XIAO_Y0 = 31.4                  # interior Y of the board's front edge

# Optional perfboard (battery junction + divider) in a card guide on the rear wall, behind the
# probe. Component side faces the probe, solder side faces the wall. Harmless if unused.
PERF_GUIDE = True
PERF_W, PERF_H = 30.0, 30.0     # measure yours
PERF_T = 1.6                    # measure yours; slot = this + PERF_SLOT_CLEAR
PERF_SLOT_CLEAR = 0.3
PERF_GRIP = 1.0                 # rail overlap on each side edge (clear of the outer hole columns)
PERF_WALL_GAP = 4.8             # board mid-plane to rear interior wall (solder side + links)
PERF_Z0 = 24.0                  # board bottom edge above the floor (clears the probe clip)

# Lid / screws
BOSS_R = 4.0
INSERT_D, INSERT_DEPTH = 4.0, 8.0   # M3 heat-set insert (use 2.6 for self-tapping)
LID_T = 3.0
SKIRT_T, SKIRT_GAP, SKIRT_H = 2.0, 0.4, 8.0
GROOVE_W, GROOVE_H = 2.0, 1.2       # gasket groove in the lid underside
SCREW_CLEAR = 3.4

# DS18B20 waterproof probe (6 x 50 mm stainless tube) goes down through the floor
# The whole steel tube is buried; only its cable passes the floor, through a PG7 cable gland
# that screws into a threaded boss (no locknut, so nothing protrudes under the floor).
DS_OFFSET_X = -33.0             # from the moisture probe centre, in the PCB plane (off its edge)
DS_TIP_DEPTH = 60.0             # tube tip below the soil surface (floor underside)
DS_TUBE_LEN, DS_TUBE_D = 50.0, 6.0
PG7_MAJOR = 12.5                # PG7 thread OD
PG7_PITCH = 1.27                # 20 TPI
PG7_CLEAR = 0.3                 # radial printing clearance; raise if the gland won't thread in
PG7_DEPTH = 0.7                 # modelled thread depth
GLAND_BOSS_D = 21.0
GLAND_BOSS_H = 6.0              # boss + floor = 9 mm of thread

VENT_D = 0.0          # e.g. 12.4 for an M12 breather vent in the rear wall; 0 = none
# Blade stakes: the blade's broad face resists rocking front-to-back (the box's narrow axis)
STAKE_W, STAKE_T = 16.0, 4.0     # blade width (X) / thickness (Y)
STAKE_DEPTH = 80.0               # below the floor, incl. tip (probe goes ~66 mm deep)
SOCKET_H = 20.0                  # socket height on the box wall
SOCKET_WALL = 3.0
STAKE_CLEAR = 0.4
# --------------------------------------------

def cube(x, y, z, at=(0, 0, 0)):
    return Manifold.cube([x, y, z]).translate(list(at))

def cyl(h, r, at=(0, 0, 0)):
    return Manifold.cylinder(h, r, r, SEG).translate(list(at))

def rbox(x, y, z, r, at=(0, 0, 0)):
    r = min(r, x / 2 - 0.01, y / 2 - 0.01)
    pts = [(r, r), (x - r, r), (r, y - r), (x - r, y - r)]
    m = Manifold.batch_hull([cyl(z, r, (px, py, 0)) for px, py in pts])
    return m.translate(list(at))

W, D = IX + 2 * WALL, IY + 2 * WALL
H = FLOOR + IZ
ox, oy, oz = WALL, WALL, FLOOR          # interior origin
cx = ox + IX / 2                         # interior centre X
sy = oy + SENSOR_Y                       # PCB plane Y (absolute)

boss_xy = [(ox + BOSS_R, oy + BOSS_R), (ox + IX - BOSS_R, oy + BOSS_R),
           (ox + BOSS_R, oy + IY - BOSS_R), (ox + IX - BOSS_R, oy + IY - BOSS_R)]

# ---------------- BOX ----------------
box = rbox(W, D, H, OUT_R) - rbox(IX, IY, IZ + 1, 1.5, (ox, oy, oz))

# screw bosses
for bx, by in boss_xy:
    box += cyl(IZ, BOSS_R, (bx, by, oz))
    box -= cyl(INSERT_DEPTH + 0.01, INSERT_D / 2, (bx, by, H - INSERT_DEPTH))

# battery bay: end stops, two snap cradles, two zip-tie tunnels (backup)
bx0 = cx - BATT_LEN / 2
by0 = oy + BATT_Y0
bcy = by0 + BATT_W / 2                       # cell axis Y
for x in (bx0 - 3, bx0 + BATT_LEN):
    box += cube(3, BATT_W, 6, (x, by0, oz))
for tx in (cx - 18, cx + 18):
    box += cube(8, BATT_W, 3.2, (tx - 4, by0, oz))
    box -= cube(4.5, BATT_W + 2, 2.0, (tx - 2.25, by0 - 1, oz))   # tie passes along Y
r_in = CELL_D / 2 + CRADLE_CLEAR
r_out = r_in + CRADLE_WALL
bcz = oz + 3.4 + r_in                        # cell sits just clear of the tie bridges
_open_z = bcz + (r_in ** 2 - (CRADLE_OPEN / 2) ** 2) ** 0.5
for cxx in (cx - CRADLE_X, cx + CRADLE_X):
    x0 = cxx - CRADLE_T / 2
    ring = Manifold.cylinder(CRADLE_T, r_out, r_out, SEG).rotate([0, 90, 0]).translate([x0, bcy, bcz])
    base = cube(CRADLE_T, 2 * r_out, bcz - oz, (x0, bcy - r_out, oz))   # square base: no overhang below the cell
    cradle = ring + base
    cradle -= Manifold.cylinder(CRADLE_T + 2, r_in, r_in, SEG).rotate([0, 90, 0]).translate([x0 - 1, bcy, bcz])
    cradle -= cube(CRADLE_T + 2, CRADLE_OPEN, r_out + 2, (x0 - 1, bcy - CRADLE_OPEN / 2, _open_z))
    box += cradle

# sensor: floor slot + two pillars (outside PCB width) for the fork
box -= cube(SLOT_W, SLOT_T, FLOOR + 2, (cx - SLOT_W / 2, sy - SLOT_T / 2, -1))
pillar_h = GROOVE_Z - FORK_T / 2           # fork top face sits in the groove
pillar_cx = PCB_W / 2 + 0.3 + PILLAR / 2
for s in (-1, 1):
    px = cx + s * pillar_cx
    box += cube(PILLAR, PILLAR, pillar_h, (px - PILLAR / 2, sy - PILLAR / 2, oz))
    box -= cyl(7, 0.9, (px, sy, oz + pillar_h - 6.5))           # M2 self-tap pilot

# DS18B20: threaded boss for a PG7 cable gland (the tube itself is buried below the floor)
dsx = cx + DS_OFFSET_X
box += cyl(GLAND_BOSS_H, GLAND_BOSS_D / 2, (dsx, sy, oz))
_thr_h = FLOOR + GLAND_BOSS_H + 2
_e = PG7_DEPTH / 2
_a = PG7_MAJOR / 2 + PG7_CLEAR - _e
_turns = _thr_h / PG7_PITCH
thread_cutter = CrossSection.circle(_a, 96).translate([_e, 0]).extrude(
    _thr_h, n_divisions=int(_turns * 48), twist_degrees=360.0 * _turns)   # +twist = right-hand thread
box -= thread_cutter.translate([dsx, sy, -1])
# 0.8 mm chamfers at both ends: stops first-layer squish closing the bottom turn and
# gives the gland a lead-in at the top
_rc = PG7_MAJOR / 2 + PG7_CLEAR
box -= Manifold.cylinder(0.8 + 0.01, _rc + 0.8, _rc, SEG).translate([dsx, sy, -0.01])
box -= Manifold.cylinder(0.8 + 0.01, _rc, _rc + 0.8, SEG).translate([dsx, sy, oz + GLAND_BOSS_H - 0.8])

# XIAO card guide on the right side
xbx = ox + IX - XIAO_WALL_GAP               # board mid-plane X
xy0 = oy + XIAO_Y0                          # board front edge Y
xy1 = xy0 + XIAO_BOARD_W                    # board rear edge Y
slot_w = XIAO_PCB_T + XIAO_SLOT_CLEAR
RAIL_X, RAIL_Y = 6.0, 4.0
for edge_y, sgn in ((xy0, -1), (xy1, 1)):   # sgn points away from the board
    ry0 = edge_y - RAIL_Y + XIAO_GRIP if sgn < 0 else edge_y - XIAO_GRIP
    box += cube(RAIL_X, RAIL_Y, XIAO_RAIL_H, (xbx - RAIL_X / 2, ry0, oz))
    sy0 = edge_y - 0.4 if sgn < 0 else edge_y - XIAO_GRIP - 0.5
    box -= cube(slot_w, XIAO_GRIP + 0.9, XIAO_RAIL_H + 1, (xbx - slot_w / 2, sy0, oz + 0.01))

# perfboard card guide on the rear wall
if PERF_GUIDE:
    pby = oy + IY - PERF_WALL_GAP               # board mid-plane Y
    pslot = PERF_T + PERF_SLOT_CLEAR
    PRAIL_X, PRAIL_FRONT = 5.0, 2.2             # rail width; rail material in front of the board
    prail_y0 = pby - pslot / 2 - PRAIL_FRONT
    prail_h = PERF_Z0 + PERF_H - 4.0            # top 4 mm of the board stands proud for a grip
    for sg in (-1, 1):
        edge = cx + sg * PERF_W / 2
        rx0 = (edge - PERF_GRIP) if sg > 0 else (edge + PERF_GRIP - PRAIL_X)
        box += cube(PRAIL_X, oy + IY + 0.5 - prail_y0, prail_h, (rx0, prail_y0, oz))
        # slot: edge clearance 0.4, runs from PERF_Z0 up through the top
        sx0 = (edge - PERF_GRIP) if sg > 0 else (edge - 0.4)
        box -= cube(PERF_GRIP + 0.4, pslot, prail_h, (sx0, pby - pslot / 2, oz + PERF_Z0))

# stake sockets, left and right, at mid-depth
SOCK_INNER = SOCKET_WALL + 2.0     # thicker on the box side so the stake head clears the wall
sock_x = STAKE_W + STAKE_CLEAR + SOCKET_WALL + SOCK_INNER
sock_y = STAKE_T + STAKE_CLEAR + 2 * SOCKET_WALL
stake_x = {}
for s_ in (-1, 1):
    x0 = -sock_x if s_ < 0 else W - 1.0
    sock = rbox(sock_x + 1.0, sock_y, SOCKET_H, 2.0, (x0, D / 2 - sock_y / 2, 0))
    hx0 = (x0 + SOCKET_WALL) if s_ < 0 else (W + SOCK_INNER)
    sock -= cube(STAKE_W + STAKE_CLEAR, STAKE_T + STAKE_CLEAR, SOCKET_H + 2,
                 (hx0, D / 2 - (STAKE_T + STAKE_CLEAR) / 2, -1))
    stake_x[s_] = hx0 + STAKE_CLEAR / 2
    box += sock

if VENT_D > 0:
    v = Manifold.cylinder(WALL + 2, VENT_D / 2, VENT_D / 2, SEG).rotate([-90, 0, 0])
    box -= v.translate([ox + 18, D - WALL - 1, H - 14])

# ---------------- LID (modelled right side up, exported flipped) ----------------
LW, LD = W + 2 * (SKIRT_GAP + SKIRT_T), D + 2 * (SKIRT_GAP + SKIRT_T)
lr = OUT_R + SKIRT_GAP + SKIRT_T
lo = -(SKIRT_GAP + SKIRT_T)
lid = rbox(LW, LD, LID_T + SKIRT_H, lr, (lo, lo, H - SKIRT_H))
lid -= rbox(W + 2 * SKIRT_GAP, D + 2 * SKIRT_GAP, SKIRT_H + 0.01, OUT_R + SKIRT_GAP,
            (-SKIRT_GAP, -SKIRT_GAP, H - SKIRT_H - 0.01))
# gasket groove over the rim centre-line
gi = WALL / 2 - GROOVE_W / 2
groove = rbox(W - 2 * gi, D - 2 * gi, GROOVE_H, OUT_R - gi, (gi, gi, H)) - \
         rbox(W - 2 * gi - 2 * GROOVE_W, D - 2 * gi - 2 * GROOVE_W, GROOVE_H + 1,
              max(OUT_R - gi - GROOVE_W, 0.5), (gi + GROOVE_W, gi + GROOVE_W, H - 0.5))
lid -= groove
for bx, by in boss_xy:
    lid -= cyl(LID_T + 2, SCREW_CLEAR / 2, (bx, by, H - 1))

# ---------------- SENSOR FORK ----------------
FORK_W = 2 * (pillar_cx + PILLAR / 2)
FORK_D = 14.0
inner = PCB_W - 2 * GROOVE_DEPTH + 0.2
fork = cube(FORK_W, FORK_D, FORK_T)
# slot opens toward -Y (the PCB's component side), runs past the PCB plane
fork -= cube(inner, FORK_D / 2 + PCB_T / 2 + 0.4 + 1, FORK_T + 2,
             (FORK_W / 2 - inner / 2, -1, -1))
for s in (-1, 1):
    fork -= cyl(FORK_T + 2, 1.2, (FORK_W / 2 + s * pillar_cx, FORK_D / 2, -1))

# ---------------- GASKET (TPU) ----------------
gasket = rbox(W - 2 * gi - 0.2, D - 2 * gi - 0.2, GROOVE_H + 0.8, OUT_R - gi, (0, 0, 0)) - \
         rbox(W - 2 * gi - 2 * GROOVE_W + 0.2, D - 2 * gi - 2 * GROOVE_W + 0.2, 5,
              max(OUT_R - gi - GROOVE_W, 0.5), (GROOVE_W - 0.2, GROOVE_W - 0.2, -1))

# ---------------- STAKE (print flat; blade lies in X-Y, thickness in Z) ----------------
_tip = 15.0
_len = STAKE_DEPTH + SOCKET_H
_hw = 4.0                         # head overhang each side, rests on the socket top
_hh = 5.0
_pts = [(STAKE_W / 2, 0), (STAKE_W, _tip), (STAKE_W, _len), (STAKE_W + _hw, _len),
        (STAKE_W + _hw, _len + _hh), (-_hw, _len + _hh), (-_hw, _len), (0, _len), (0, _tip)]
stake = CrossSection([_pts]).extrude(STAKE_T)

def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                           faces=np.asarray(mesh.tri_verts), process=False)

if __name__ == "__main__":
    import os
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "stl")
    os.makedirs(out, exist_ok=True)
    lid_print = lid.rotate([180, 0, 0])
    lid_print = lid_print.translate([0, 0, -lid_print.bounding_box()[2]])
    parts = {"box": box, "lid": lid_print, "sensor_fork": fork, "gasket_tpu": gasket,
             "stake": stake}
    for name, m in parts.items():
        t = to_trimesh(m)
        t.export(os.path.join(out, f"{name}.stl"))
        print(f"{name}: watertight={t.is_watertight} vol={t.volume/1000:.1f} cm3 "
              f"extent={np.round(t.extents, 1)}")
