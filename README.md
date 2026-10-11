# Pickleball Robot

This repository contains the current electronics design and control software for the pickleball robot.

## Repository layout

```text
.
|-- cad/                    # Reserved for future CAD source files
|-- firmware/
|   |-- esp32/              # ESP-IDF motor, servo, Wi-Fi, and web controller
|   `-- raspberry_pi/       # Camera stream and USB-serial bridge service
`-- pcb/                    # Current KiCad schematic, board, and project files
```

Generated manufacturing outputs, temporary files, build artifacts, old controller designs, and superseded experiments are intentionally excluded.

## ESP32 firmware

The ESP32 firmware provides:

- Wi-Fi access point and phone-based drive controls
- Left and right wheel-motor control
- Four servo outputs
- Coordinated swing commands
- USB serial control for the Raspberry Pi
- A command watchdog that stops the wheels if control is lost

Requirements:

- ESP-IDF 5.3.1
- Target: ESP32 / ESP32-PICO-D4
- Default serial port in the current instructions: `COM6`

Build and flash from an ESP-IDF terminal:

```powershell
cd firmware/esp32
idf.py -p COM6 build flash monitor
```

See [`firmware/esp32/README.md`](firmware/esp32/README.md) for pin assignments, controls, and serial commands.

## Raspberry Pi service

The Raspberry Pi service exposes the Pi camera stream and forwards HTTP control commands to the ESP32 over USB serial.

See [`firmware/raspberry_pi/README.md`](firmware/raspberry_pi/README.md) for details.

## PCB design

Open [`pcb/my turn.kicad_pro`](pcb/my%20turn.kicad_pro) in KiCad. The PCB folder includes:

- `my turn.kicad_pro` — KiCad project
- `my turn.kicad_sch` — schematic source
- `my turn.kicad_pcb` — PCB layout source
- `fp-lib-table` and `Custom.pretty/` — required local footprint library

Fabrication files are not checked in. Generate fresh Gerbers, drill files, placement data, and BOM files from the current KiCad sources when preparing a board revision.

## CAD

The `cad/` directory is reserved for future mechanical source files. Keep editable CAD sources here rather than generated previews or temporary exports.

## Safety

Keep the physical emergency stop accessible during testing. Verify servo limits with the mechanism unloaded, keep clear of the swing mechanism, and test wheel direction at low power after firmware or wiring changes.
