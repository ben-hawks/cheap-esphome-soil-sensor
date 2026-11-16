# Build guide

## Bill of materials

Quantities are per sensor.

| Item | Qty | Notes |
| --- | --- | --- |
| Seeed XIAO ESP32-C6 | 1 | No headers. The wires solder straight to the pads. |
| Capacitive soil moisture sensor v2.0 | 1 | Check the timer chip: a TLC555 works at 3.3 V; NE555 versions are unreliable. |
| DS18B20 waterproof probe, 6 × 50 mm stainless tube | 1 | Usually sold with a 1 m cable. Coil the spare inside the box. |
| PG7 nylon cable gland (3–6.5 mm cable) | 1 | Screws into a threaded boss in the floor. No locknut needed. |
| 3.7 V wrapped 18650 pack with JST PH leads (~19 mm × 69 mm) | 1 | Snaps into the cradles |
| JST PH 2.0 2-pin pigtail (mating) | 1 | Goes on the XIAO's BAT pads, so the pack unplugs |
| 1 MΩ resistor | 2 | Battery-voltage divider |
| 100 nF ceramic capacitor | 1 | Across the lower divider resistor. Needed because 1 MΩ is too weak a source for the ADC on its own. |
| 4.7 kΩ resistor | 1 | DS18B20 pull-up. **Check it's kΩ, not Ω:** yellow-violet-black-*brown* on a 5-band resistor. |
| 26–28 AWG silicone wire | ~30 cm | |
| M3 heat-set insert (4.0 mm hole) | 4 | Lid screws |
| M3 × 10 pan-head screw + nylon washer | 4 | |
| M2 × 6 self-tapping screw | 2 | Fixes the probe clip to its pillars |
| Gasket: printed TPU or 2 mm silicone cord | 1 | About 300 mm of cord |
| Neutral-cure silicone | — | Seals the probe slot in the floor |
| Conformal coat or clear nail polish | — | Probe edges and component area |
| 6 mm rod or long screwdriver | — | For installing only: makes the pilot hole for the DS18B20 tube |
| Zip tie, ≤ 4 mm | 1 | Optional backup for the battery |
| M12 breather vent | optional | Only if condensation shows up. Set `VENT_D = 12.4`. |

## Printing

Print everything in **ASA**, except the optional TPU gasket. ASA is UV-stable and stays stiff in a hot box in full sun. PETG will last a season or two, but avoid PLA because it softens around 55–60 °C. Choose a light colour if you can: a dark box runs much hotter in the sun, which is bad for the cell and skews the soil temperature underneath.

None of the parts need supports.

| Part | Orientation | Notes |
| --- | --- | --- |
| `box.stl` | Floor on the bed | 6 perimeters (2.4 mm walls), 15–20% infill, 5 mm brim. 144 × 63 × 59 mm including the stake sockets. |
| `lid.stl` | Top face on the bed (already flipped) | 5 mm brim |
| `sensor_fork.stl` | Flat | Print this first: in about 5 minutes it tells you whether the clip fits your probe's grooves |
| `stake.stl` | Flat | Print 2. 100% infill or 6+ perimeters. |
| `gasket_tpu.stl` | Flat | TPU, optional |

On a Bambu X1C, print in an enclosed chamber with little or no part cooling, the bed at 100–110 °C, and the nozzle at 240–260 °C. 0.2 mm layers are fine, even for the 1.27 mm-pitch gland thread.

**Fit checks after the first print:**

- **PG7 gland:** screw it into its floor boss. If it binds, raise `PG7_CLEAR` by 0.1.
- **Battery cradles:** press the cell in. If it's too stiff, set `CRADLE_OPEN` to 18.0; if it's loose, 17.2.
- **XIAO guide:** slide the board into its rails. The slots assume a 1.0 mm PCB, so measure yours and adjust `XIAO_PCB_T`.

Every dimension is a parameter at the top of [`enclosure/soil_enclosure.py`](../enclosure/soil_enclosure.py). After changing one, regenerate the STLs:

```sh
pip install manifold3d trimesh numpy
python3 enclosure/soil_enclosure.py   # writes enclosure/stl/
```

## Layout

![Top-down layout, lid off](images/plan.png)

- **Battery:** lies across the front of the box in two snap cradles.
- **Moisture probe:** stands edge-on in the middle and passes through a slot in the floor. The clip locks its side grooves so the floor sits 13 mm below the probe's "never bury past this" line, inside the maker's recommended band.
- **XIAO:** stands in a card guide on the right, USB-C up, 13 mm off the wall. Its wired top side faces the open middle of the box; its flat underside faces the wall.
- **DS18B20:** the tube is buried 33 mm to the left of the probe centre, in the same plane as the probe's board, well clear of the probe's sensing field. Its tip is 6 cm down.

## Assembly

1. **Inserts and gland.** Press the four M3 heat-set inserts into the corner bosses. Screw the PG7 gland body into the floor boss from inside.
2. **Coat the probe.** Paint the cut PCB edges along the whole probe, and the component area, with conformal coat or nail polish. Leave the connector clean.
3. **Solder the XIAO** following [soldering.md](soldering.md). Before soldering the DS18B20, feed its cable up through the gland body, seal insert and cap: the steel tube won't fit through afterwards.
4. **Flash and bench test.** See [firmware.md](firmware.md).
5. **Fit the probe.** Push it down through the floor slot from inside, components facing the battery side, until the grooves line up with the pillar tops.
6. **Fit the clip.** Slide the fork in from the battery side so its tines enter both grooves, then screw it to the pillars with two M2 screws.
7. **Mark the DS18B20 depth.** With the tube hanging below the floor, set its tip 60 mm below the floor's underside. Mark the cable where it leaves the top of the gland body.
8. **Seal the probe slot** with neutral-cure silicone, inside and out, and let it cure.
9. **Battery.** Press the pack down into the two cradles with its leads along the top, then plug it in.
10. **XIAO.** Slide it straight down into the card guide, USB-C up, wired side facing the probe. Coil the spare DS18B20 cable in the rear-left corner.
11. **Install.** With the lid off, unscrew the gland cap and pull the steel tube up into the box through the gland body. Slide a stake into each socket and press the box down until the floor sits flat on the soil. Push the 6 mm rod down through the gland body about 6 cm and pull it out. Lower the tube into the hole until the cable mark reaches the gland, then tighten the cap. Firm the soil around the edge of the floor.
12. **Lid.** Seat the gasket, then fit the lid with four M3 × 10 screws and washers. Tighten evenly until the gasket just compresses.
