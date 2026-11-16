# Firmware

[`firmware/soil-sensor.yaml`](../firmware/soil-sensor.yaml) is a complete ESPHome config. It has been tested on ESPHome 2026.10.2 with Home Assistant 2026.11 and a Home Assistant Yellow running the OpenThread Border Router app.

## What it does on each wake

1. **Battery check, before the network starts.** Below `battery_low_v` (3.40 V) the next sleep lasts 24 h; below `battery_cutoff_v` (3.30 V), 7 days.
2. **Join Thread** as a minimal end device and register with the border router.
3. **Wait for Home Assistant.** It waits up to 45 s for Home Assistant specifically: the trigger is the stay-awake toggle's state, which only Home Assistant sends. Other API clients, such as the dashboard's log viewer, can connect and watch, but they don't trigger a report or a sleep.
4. **Report.** It reads the battery and starts the DS18B20 conversion, powers the moisture probe from D2 for `sensor_settle`, reads it, and powers it off.
5. **Sleep or stay awake.** If the stay-awake toggle is off, it tells Home Assistant it's going to sleep, waits up to 5 s for it to hang up, and sleeps for `sleep_time` (15 min). Home Assistant then keeps showing the last readings instead of marking them unavailable. If the toggle is on, it stays awake until you turn the toggle off.

A 60 s failsafe puts it to sleep if Thread or Home Assistant never comes up. An OTA update blocks sleep while it runs, so a slow update over Thread can't be cut off.

## Setup

1. **Add the config.** Copy `soil-sensor.yaml` into your ESPHome configs. For each sensor, change `name` and `friendly_name` in `substitutions`.
2. **Add the secrets** to your ESPHome `secrets.yaml` (see [`secrets.example.yaml`](../firmware/secrets.example.yaml)):
   - `thread_tlv` is your Thread network's active dataset as hex. In Home Assistant, go to Settings → Devices & services → Thread → (your network) → ⋮ → *Active dataset TLVs*.
   - `api_encryption_key` is a 32-byte base64 key. You can share one across devices.
3. **First flash over USB.** Download the factory image from the ESPHome dashboard (⋮ → Download → Factory format) and flash it with [web.esphome.io](https://web.esphome.io). If the board is asleep, hold BOOT while you plug it in.
4. **Add it to Home Assistant.** It shows up as a discovered ESPHome device. Add it using your API key.
5. **Create the stay-awake helper.** Go to Settings → Devices & services → Helpers → Create helper → Toggle, and name it "Soil sensors stay awake" (`input_boolean.soil_sensors_stay_awake`). One helper serves every sensor. Without it, the sensors still work and simply sleep as normal.

## Calibration

Calibration is stored on each sensor and edited from Home Assistant, so you never reflash.

1. **Wake it.** Turn the stay-awake toggle on, then wait for the next wake or press reset.
2. **Dry point:** with the probe in dry air, enter the **Soil moisture raw** reading as **Moisture calibration dry** on the device page (Configuration section).
3. **Wet point:** dip the probe in water up to the line and wait for a fresh reading. Enter it as **Moisture calibration wet**. The percentage recalculates immediately.
4. **Back to normal:** turn the toggle off.

Calibrate each probe separately, because these boards differ by 0.1–0.3 V. Example from one unit: 2.52 V dry, 0.80 V wet.

Air-to-water calibration gives every sensor the same scale, but it isn't true volumetric water content: real soil sits somewhere in the middle. For watering decisions, set your thresholds from what each sensor reads when you know the soil is dry or properly watered.

## OTA updates

1. Turn the stay-awake toggle on and wait for the sensor's next wake (or press reset).
2. Install from the ESPHome dashboard. An update over Thread takes about 2 minutes.
3. **Keep USB serial closed for the first 60 s after the update reboots.** The browser reconnecting over USB resets the board, and a new build that resets before 60 s gets rolled back by the bootloader. Network logs from the dashboard are fine.
4. Turn the toggle off.

## Battery

- **Divider:** 2 × 1 MΩ plus 100 nF, read on D0 with 8 samples. Check the reading against a meter once and adjust `multiply` if it's off by more than about 0.05 V.
- **Protection:** under 3.40 V the sensor drops to one wake a day; under 3.30 V, one a week. Charge it over USB-C with the lid off; it returns to normal on the next wake after charging.
- **Alerts:** a Home Assistant automation on `Battery voltage < 3.45` gives a few days' warning. Example:

```yaml
alias: Soil sensor battery low
triggers:
  - trigger: numeric_state
    entity_id: sensor.soil_sensor_1_battery_voltage
    below: 3.45
actions:
  - action: notify.notify
    data:
      message: "{{ state_attr(trigger.entity_id, 'friendly_name') }} is at {{ trigger.to_state.state }} V. Time to charge."
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Found no devices!` (one-wire) | Bad or missing pull-up | See [soldering.md](soldering.md#troubleshooting) |
| `task_wdt` reset around 60 s | Seen while the one-wire pull-up was 4.7 Ω, fighting the bus | Fix the pull-up |
| Sensor sleeps even though the toggle is on | (Old firmware) only a *change* of the toggle was handled | Fixed: the toggle's state is checked on every report |
| New build reverts to the old one (`OTA rollback detected!`) | USB serial reset the board within 60 s of the update | Keep USB logs closed for the first minute |
| Home Assistant doesn't reconnect after several quick resets; border router log shows `NoAck` to the sensor and the sensor logs `SRP ... ResponseTimeout` | The border router still routes to the sensor's previous radio address for a few minutes | Leave it alone for a wake cycle or two. Normal 15-minute wakes aren't affected. |
| Entities go unavailable about 90 s after each report; the Home Assistant log shows `Ping response not received after 90.0 seconds` and `disconnected (expected=False)` | ESPHome's sleep path turns the Thread radio off before the disconnect message gets out | Fixed by the `go_to_sleep` script, which says goodbye before sleeping |
| Dashboard says `Timeout while connecting` | The sensor is asleep | Normal. Turn on the toggle to keep it awake. |

## Tunables (`substitutions`)

| Name | Default | Purpose |
| --- | --- | --- |
| `sleep_time` | `15min` | Time between reports |
| `sensor_settle` | `1s` | Moisture probe warm-up before reading |
| `moisture_dry_v` / `moisture_wet_v` | `2.52` / `1.20` | Starting calibration for a new board; the real values are set in Home Assistant |
| `stay_awake_entity` | `input_boolean.soil_sensors_stay_awake` | Toggle that keeps the sensor awake |
| `battery_low_v` / `battery_cutoff_v` | `3.40` / `3.30` | Battery protection thresholds |
