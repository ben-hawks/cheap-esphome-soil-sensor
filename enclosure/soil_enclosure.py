"""
Outdoor soil-sensor enclosure: XIAO ESP32-C6 + wrapped 18650 pack (69 x ~19 mm) +
Capacitive Soil Moisture Sensor v2.0 (22 x 100 mm PCB) + DS18B20 probe.

Compact layout (top view, front at the bottom):

    rear   [PG7 gland]  [ probe in latch rails ]
           [ XIAO | perfboard ]  <- on a lift-out carrier, standing over the cell
    front  [========= 18650 in two snap cradles =========]
           [ stake sleeve ]          [ stake sleeve ]

The probe passes through a slot in the floor. Two card-guide rails grip its side edges
from the floor up, so it can't rock, and a snap latch in each rail clicks into the
probe's side grooves to set the depth. The floor's underside sits 13 mm below the probe's
warning line, inside the maker's recommended band, so the box rests on the soil.

A board carrier (separate part) stands over the battery: its legs drop into channels on the
end walls and double as the cell's end stops. The XIAO and the optional perfboard slide into
slotted posts on it. Lift it out (boards and all) to get at the cell.

Two printed blade stakes drop through sealed sleeves along the front wall, inside the box.
A DS18B20 waterproof probe (6 x 50 mm tube) is buried whole beside the moisture probe;
its cable enters through a PG7 gland screwed into a threaded boss in the floor.

Outputs (STL, mm):
  box.stl            print floor-down, no supports
  lid.stl            already flipped (top face on the bed), no supports
  board_carrier.stl  already laid flat (back face on the bed), no supports
  gasket_tpu.stl     optional, TPU, sits in the lid groove
  stake.stl          print 2, flat

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
IX, IY, IZ = 78.0, 48.0, 58.0   # interior size (X width, Y depth, Z height)
OUT_R = 4.0           # outer corner radius

# Battery: ELXJAR wrapped 18650 pack with leads, ~69 mm long, ~19 mm cell, lying along X
# near the front wall in two snap cradles (press it down through the opening, leads on top).
CELL_LEN = 69.0
CELL_D = 19.0                   # measured cell diameter
CELL_Y = 18.0                   # interior Y of the cell axis
CELL_LIFT = 1.0                 # cell bottom above the floor
CRADLE_CLEAR = 0.2              # radial clearance in the cradle
CRADLE_WALL = 2.2               # cradle ring thickness
CRADLE_OPEN = 17.6              # snap opening; ~1.4 mm narrower than the cell
CRADLE_T = 6.0                  # cradle thickness along the cell
CRADLE_X = 15.0                 # cradles at centre +/- this (kept clear of the PG7 gland)

# Sensor PCB
PCB_W, PCB_T = 22.0, 1.6
SLOT_W, SLOT_T = 22.6, 2.0      # floor slot (seal it with silicone after fitting)
SENSOR_Y = 37.0                 # interior Y of the PCB plane
GROOVE_DEPTH = 1.2              # how far each side groove cuts into the PCB edge
GROOVE_H = 2.2                  # groove height
# Probe depth, measured from the top edge of the sensor PCB (from the product diagram):
GROOVE_FROM_TOP = 19.8          # side grooves
SOIL_FROM_TOP = 44.0            # floor underside = soil surface; recommended band ~41-64,
                                # red warning line ~31 (never bury past it)
GROOVE_Z = SOIL_FROM_TOP - FLOOR - GROOVE_FROM_TOP   # groove centre above floor's top face

# Probe rails + snap latches. Each rail: two cheeks that grip the PCB faces from the floor
# up (stops rocking), and behind them a springy beam whose tooth clicks into the side groove.
# The tooth's flat underside stops the probe being pushed up (soil pushing back while you
# press the box in); its sloped top lets the probe snap in from above.
RAIL_ENGAGE = 1.5               # how far the cheeks overlap the PCB edge
RAIL_SLOT_CLEAR = 0.3           # slot = PCB_T + this
CHEEK_T = 3.0                   # cheek thickness (Y)
BEAM_T = 1.6                    # latch beam thickness (X): stiffness
BEAM_GAP = 0.6                  # PCB edge to beam face
BEAM_HW = 2.5                   # latch beam half-width (Y)
LATCH_SLIT = 0.4                # clearance around the beam
LATCH_BASE = 3.0                # beam is anchored below this height
TOOTH_W = 1.4                   # tooth width (Y), fits the slot
TOOTH_REACH = 0.2               # tooth tip stops this short of the groove bottom
RAIL_ABOVE = 4.5                # rails and beams continue this far above the groove (finger tab)

# Board carrier (separate part) over the cell
CARRIER_T = 8.0                 # carrier thickness (Y), centred on the cell axis
CARRIER_Z0 = 21.0               # crossbar underside above the floor (cell top is ~20.2)
CROSSBAR_H = 3.0
LEG_T = 3.2                     # leg thickness (X); legs also stop the cell sliding
LEG_CLEAR = 0.3                 # leg to end wall / channel ribs
POST_W = 4.0
CARD_SLOT_DEPTH = 1.4           # board-edge slots: grip 1.0 + 0.4 clearance
XIAO_BOARD_W = 17.8
XIAO_PCB_T = 1.0                # measure yours
XIAO_GRIP_H = 8.0               # grips only the unused bottom pin rows (D4-D6 / D7-D9)
PERF_W, PERF_H = 30.0, 30.0     # measure yours
PERF_T = 1.6                    # measure yours
CARD_SLOT_CLEAR = 0.3

# Lid / screws
BOSS_R = 4.0
INSERT_D, INSERT_DEPTH = 4.0, 8.0   # M3 heat-set insert (use 2.6 for self-tapping)
LID_T = 3.0
SKIRT_T, SKIRT_GAP, SKIRT_H = 2.0, 0.4, 8.0
GROOVE_W, GROOVE_H_LID = 2.0, 1.2   # gasket groove in the lid underside
SCREW_CLEAR = 3.4

# DS18B20 waterproof probe (6 x 50 mm stainless tube) goes down through the floor
# The whole steel tube is buried; only its cable passes the floor, through a PG7 cable gland
# that screws into a threaded boss (no locknut, so nothing protrudes under the floor).
DS_OFFSET_X = -24.0             # from the moisture probe centre, in the PCB plane (off its edge)
DS_TIP_DEPTH = 60.0             # tube tip below the soil surface (floor underside)
DS_TUBE_LEN, DS_TUBE_D = 50.0, 6.0
PG7_MAJOR = 12.5                # PG7 thread OD
PG7_PITCH = 1.27                # 20 TPI
PG7_CLEAR = 0.3                 # radial printing clearance; raise if the gland won't thread in
PG7_DEPTH = 0.7                 # modelled thread depth
GLAND_BOSS_D = 17.5
GLAND_BOSS_H = 6.0              # boss + floor = 9 mm of thread
GLAND_HEX_R = 8.7               # PG7 body/cap across corners / 2 (for clearance checks)

VENT_D = 0.0          # e.g. 12.4 for an M12 breather vent in the rear wall; 0 = none
# Blade stakes in sleeves along the front wall; the broad face resists front-to-back rocking
STAKE_W, STAKE_T = 16.0, 4.0     # blade width (X) / thickness (Y)
STAKE_DEPTH = 80.0               # below the floor, incl. tip (probe goes ~54 mm deep)
STAKE_X = 18.0                   # sleeves at centre +/- this
SLEEVE_H = 20.0                  # sleeve height above the floor
SLEEVE_WALL = 2.0
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

def box_x(x0, x1, y0, y1, z0, z1):
    """Axis-aligned block from min/max corners (order-insensitive)."""
    xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1)); za, zb = sorted((z0, z1))
    return cube(xb - xa, yb - ya, zb - za, (xa, ya, za))

W, D = IX + 2 * WALL, IY + 2 * WALL
H = FLOOR + IZ
ox, oy, oz = WALL, WALL, FLOOR          # interior origin
cx = ox + IX / 2                         # interior centre X
sy = oy + SENSOR_Y                       # PCB plane Y (absolute)
bcy = oy + CELL_Y                        # cell axis Y (absolute)

boss_xy = [(ox + BOSS_R, oy + BOSS_R), (ox + IX - BOSS_R, oy + BOSS_R),
           (ox + BOSS_R, oy + IY - BOSS_R), (ox + IX - BOSS_R, oy + IY - BOSS_R)]

# ---------------- BOX ----------------
box = rbox(W, D, H, OUT_R) - rbox(IX, IY, IZ + 1, 1.5, (ox, oy, oz))

# screw bosses
for bx, by in boss_xy:
    box += cyl(IZ, BOSS_R, (bx, by, oz))
    box -= cyl(INSERT_DEPTH + 0.01, INSERT_D / 2, (bx, by, H - INSERT_DEPTH))

# battery: two snap cradles (the carrier legs are the end stops)
r_in = CELL_D / 2 + CRADLE_CLEAR
r_out = r_in + CRADLE_WALL
bcz = oz + CELL_LIFT + r_in
_open_z = bcz + (r_in ** 2 - (CRADLE_OPEN / 2) ** 2) ** 0.5
for cxx in (cx - CRADLE_X, cx + CRADLE_X):
    x0 = cxx - CRADLE_T / 2
    ring = Manifold.cylinder(CRADLE_T, r_out, r_out, SEG).rotate([0, 90, 0]).translate([x0, bcy, bcz])
    base = cube(CRADLE_T, 2 * r_out, bcz - oz, (x0, bcy - r_out, oz))   # square base: no overhang below the cell
    cradle = ring + base
    cradle -= Manifold.cylinder(CRADLE_T + 2, r_in, r_in, SEG).rotate([0, 90, 0]).translate([x0 - 1, bcy, bcz])
    cradle -= cube(CRADLE_T + 2, CRADLE_OPEN, r_out + 2, (x0 - 1, bcy - CRADLE_OPEN / 2, _open_z))
    box += cradle

# stake sleeves along the front wall (the wall is the sleeve's front face)
st_hx = (STAKE_W + STAKE_CLEAR) / 2
st_ty = STAKE_T + STAKE_CLEAR
stake_x = {}
for s in (-1, 1):
    sxc = cx + s * STAKE_X
    box += box_x(sxc - st_hx - SLEEVE_WALL, sxc + st_hx + SLEEVE_WALL, oy - 0.5, oy + st_ty + SLEEVE_WALL,
                 oz - 0.5, oz + SLEEVE_H)
    stake_x[s] = sxc
for s in (-1, 1):
    sxc = cx + s * STAKE_X
    box -= box_x(sxc - st_hx, sxc + st_hx, oy, oy + st_ty, -1, oz + SLEEVE_H + 1)

# carrier leg channels: a pair of ribs on each end wall
leg_y0, leg_y1 = bcy - CARRIER_T / 2, bcy + CARRIER_T / 2
RIB_T, RIB_D, RIB_H = 1.2, 2.0, 30.0
for xw, sgn in ((ox, 1), (ox + IX, -1)):
    for yy in (leg_y0 - LEG_CLEAR - RIB_T, leg_y1 + LEG_CLEAR):
        box += box_x(xw - sgn * 0.5, xw + sgn * RIB_D, yy, yy + RIB_T, oz - 0.5, oz + RIB_H)

# probe: floor slot + two latch rails
box -= cube(SLOT_W, SLOT_T, FLOOR + 2, (cx - SLOT_W / 2, sy - SLOT_T / 2, -1))
slot_hw = (PCB_T + RAIL_SLOT_CLEAR) / 2
x_in = PCB_W / 2 - RAIL_ENGAGE                 # cheek inner face (|x| from cx)
x_beam = PCB_W / 2 + BEAM_GAP                  # beam inner face
x_beam_out = x_beam + BEAM_T
x_cheek_out = x_beam - LATCH_SLIT              # cheeks stop short of the beam
x_rail_out = x_beam_out + 1.4                  # frame around the beam's sides
rail_top = GROOVE_Z + RAIL_ABOVE
y_cheek = slot_hw + CHEEK_T                    # rail half-depth (Y)
zb = oz + GROOVE_Z - GROOVE_H / 2 + 0.1        # tooth underside
for s in (-1, 1):
    X = lambda u: cx + s * u
    # base block the beam grows from
    box += box_x(X(x_in), X(x_rail_out), sy - y_cheek, sy + y_cheek, oz - 0.5, oz + LATCH_BASE)
    for t in (-1, 1):
        # cheek on each face of the PCB
        box += box_x(X(x_in), X(x_cheek_out), sy + t * slot_hw, sy + t * y_cheek, oz - 0.5, oz + rail_top)
        # side frame beside the beam (joins the cheek, leaves the beam free)
        box += box_x(X(x_in), X(x_rail_out), sy + t * (BEAM_HW + LATCH_SLIT), sy + t * y_cheek,
                     oz - 0.5, oz + rail_top)
    # the springy beam
    box += box_x(X(x_beam), X(x_beam_out), sy - BEAM_HW, sy + BEAM_HW, oz + LATCH_BASE - 0.5, oz + rail_top)
    # tooth: flat underside, 45 deg lead-in on top
    tip = PCB_W / 2 - GROOVE_DEPTH + TOOTH_REACH
    root = x_beam + 0.3
    prof = CrossSection([[(tip, 0.0), (root, 0.0), (root, 0.6 + (root - tip)), (tip, 0.6)]])
    tooth = prof.extrude(TOOTH_W).rotate([90, 0, 0]).translate([0, TOOTH_W / 2, 0])  # profile in XZ, width in Y
    if s < 0:
        tooth = tooth.mirror([1, 0, 0])
    box += tooth.translate([cx, sy, zb])

# the PCB passes through both base blocks
box -= box_x(cx - PCB_W / 2 - 0.4, cx + PCB_W / 2 + 0.4, sy - slot_hw, sy + slot_hw, oz - 1, oz + LATCH_BASE + 0.01)

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

if VENT_D > 0:
    v = Manifold.cylinder(WALL + 2, VENT_D / 2, VENT_D / 2, SEG).rotate([-90, 0, 0])
    box -= v.translate([cx + 18, D - WALL - 1, H - 14])

# ---------------- BOARD CARRIER (modelled in place; exported lying on its back) ----------------
# XIAO on the left (USB-C up, top side toward the probe), perfboard on the right
# (component side toward the probe). Positions are |x| from cx.
cz0, cz1 = oz + CARRIER_Z0, oz + CARRIER_Z0 + CROSSBAR_H     # crossbar; boards stand on cz1
leg_out = IX / 2 - LEG_CLEAR
leg_in = leg_out - LEG_T
GRIP = CARD_SLOT_DEPTH - 0.4                                 # board edge inside its member
xiao_x0 = -(leg_in + GRIP)                                   # board edges (relative to cx)
xiao_x1 = xiao_x0 + XIAO_BOARD_W
perf_x1 = leg_in + GRIP
perf_x0 = perf_x1 - PERF_W
xiao_top = cz1 + XIAO_GRIP_H
perf_top = cz1 + PERF_H - 4.0                                # top 4 mm stands proud
members = [
    (-leg_out, -leg_in, oz, xiao_top),                       # left leg
    (leg_in, leg_out, oz, perf_top),                         # right leg
    (-leg_out, leg_out, cz0, cz1),                           # crossbar
    (xiao_x1 - GRIP, xiao_x1 - GRIP + POST_W, cz1 - 0.5, xiao_top),   # post A (XIAO right edge)
    (perf_x0 + GRIP - POST_W, perf_x0 + GRIP, cz1 - 0.5, perf_top),   # post B (perfboard left edge)
]
carrier = None
for a, b, z0_, z1_ in members:
    m = box_x(cx + a, cx + b, leg_y0, leg_y1, z0_, z1_)
    carrier = m if carrier is None else carrier + m
def card_slot(edge, inward, pcb_t, z0_, z1_):
    """Slot for a board edge at x=edge (rel. cx); the member lies on the side `inward` (+1/-1)."""
    hw = (pcb_t + CARD_SLOT_CLEAR) / 2
    return box_x(cx + edge - inward * (GRIP + 0.5), cx + edge + inward * 0.4,
                 bcy - hw, bcy + hw, z0_, z1_ + 1)
carrier -= card_slot(xiao_x0, -1, XIAO_PCB_T, cz1, xiao_top)
carrier -= card_slot(xiao_x1, +1, XIAO_PCB_T, cz1, xiao_top)
carrier -= card_slot(perf_x0, -1, PERF_T, cz1, perf_top)
carrier -= card_slot(perf_x1, +1, PERF_T, cz1, perf_top)

# ---------------- LID (modelled right side up, exported flipped) ----------------
LW, LD = W + 2 * (SKIRT_GAP + SKIRT_T), D + 2 * (SKIRT_GAP + SKIRT_T)
lr = OUT_R + SKIRT_GAP + SKIRT_T
lo = -(SKIRT_GAP + SKIRT_T)
lid = rbox(LW, LD, LID_T + SKIRT_H, lr, (lo, lo, H - SKIRT_H))
lid -= rbox(W + 2 * SKIRT_GAP, D + 2 * SKIRT_GAP, SKIRT_H + 0.01, OUT_R + SKIRT_GAP,
            (-SKIRT_GAP, -SKIRT_GAP, H - SKIRT_H - 0.01))
# gasket groove over the rim centre-line
gi = WALL / 2 - GROOVE_W / 2
groove = rbox(W - 2 * gi, D - 2 * gi, GROOVE_H_LID, OUT_R - gi, (gi, gi, H)) - \
         rbox(W - 2 * gi - 2 * GROOVE_W, D - 2 * gi - 2 * GROOVE_W, GROOVE_H_LID + 1,
              max(OUT_R - gi - GROOVE_W, 0.5), (gi + GROOVE_W, gi + GROOVE_W, H - 0.5))
lid -= groove
for bx, by in boss_xy:
    lid -= cyl(LID_T + 2, SCREW_CLEAR / 2, (bx, by, H - 1))

# ---------------- GASKET (TPU) ----------------
gasket = rbox(W - 2 * gi - 0.2, D - 2 * gi - 0.2, GROOVE_H_LID + 0.8, OUT_R - gi, (0, 0, 0)) - \
         rbox(W - 2 * gi - 2 * GROOVE_W + 0.2, D - 2 * gi - 2 * GROOVE_W + 0.2, 5,
              max(OUT_R - gi - GROOVE_W, 0.5), (GROOVE_W - 0.2, GROOVE_W - 0.2, -1))

# ---------------- STAKE (print flat; blade lies in X-Y, thickness in Z) ----------------
_tip = 15.0
_len = STAKE_DEPTH + FLOOR + SLEEVE_H
_hw = 4.0                         # head overhang each side, rests on the sleeve top
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
    carrier_print = carrier.rotate([90, 0, 0])               # back face (+Y) down
    bb = carrier_print.bounding_box()
    carrier_print = carrier_print.translate([-bb[0], -bb[1], -bb[2]])
    parts = {"box": box, "lid": lid_print, "board_carrier": carrier_print, "gasket_tpu": gasket,
             "stake": stake}
    for name, m in parts.items():
        t = to_trimesh(m)
        t.export(os.path.join(out, f"{name}.stl"))
        print(f"{name}: watertight={t.is_watertight} vol={t.volume/1000:.1f} cm3 "
              f"extent={np.round(t.extents, 1)}")
