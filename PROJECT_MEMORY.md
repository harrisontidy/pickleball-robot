# Pickleball robot — current project memory

Updated: 2026-07-12. This file contains only the current design; superseded wiring is intentionally removed.

## Goal and compute

The robot is a mobile pickleball player that detects an incoming ball, moves into position, and swings a real paddle. Raspberry Pi 5 performs vision/planning, with a Hailo-8L available later. ESP32-PICO-KIT V4.1 handles real-time wheels, encoders, sensing, and servo commands.

## Supplied hardware

- 3S 11.1 V nominal, 12.6 V full, 2000 mAh LiPo with XT60.
- Two Huyuduo GA25-370 12 V, 500 RPM brushed gearmotors with quadrature encoders.
- ESP32-PICO-KIT V4.1 carrier: 2.54 mm pitch, 17 populated positions per side, 17.78 mm row spacing.
- Main swing: Miuzei 25KG 270° digital servo at 8.4 V.
- Elbow: MG996R at 6 V.
- Wrist: MG90S at 4.85 V from its dedicated U16 LDO.

## Current electrical architecture

- J1 is a board-mounted AMASS XT60PW-M input; its library footprint is pin 1 negative/GND and pin 2 positive/BAT_RAW.
- F1 is the 15 A main battery fuse.
- U12 LTC4365 and back-to-back IRLB4030PBF MOSFETs disconnect the whole board below approximately 9.62 V, reconnect near 10.10 V, and reject input above approximately 13.79 V.
- `VBAT_SW` is the protected output and powers Pi and logic.
- The external E-stop uses Schneider XB5AS8442 NC contacts to control a Panasonic CB1aF-RM-12V-A-5 resistor-suppressed relay coil from J21. The relay's 40 A NO contact bridges J18; pressing E-stop or breaking the coil loop removes `ACT_VBAT`.
- D21 clamps actuator-bus regenerative transients locally.
- U1 makes the ESP32/logic 5 V rail.
- U4 makes approximately 5.1 V for Raspberry Pi J9. Its EN pin uses a divider rather than direct battery voltage.
- U10 makes 6 V for the MG996R at J13. U11 makes 8.4 V for J12. U16 derives 4.85 V from the 6 V rail for the MG90S at J14.
- Pi GPIO17 controls `SERVO_POWER_ENABLE`, which defaults low. It does not switch wheel power; wheel startup safety comes from hardware pull-downs and the E-stop.
- The cutoff monitors total pack voltage; it is not a balance charger or per-cell BMS. Charge with a proper 3S balance charger and periodically check individual cells.

## Canonical ESP32 assignments

| Function | GPIO |
|---|---:|
| I2C SDA / SCL | 21 / 22 |
| Pi UART RX / TX | 18 / 19 |
| Aggregated motor diagnostic | 23 |
| Servo OE | 32 |
| Left PWM / INA / INB | 25 / 26 / 27 |
| Right PWM / INA / INB | 14 / 13 / 4 |
| Battery ADC | 33 |
| Left / right current ADC | 36 / 39 |
| Left encoder A / B | 34 / 35 |
| Right encoder A / B | 37 / 38 |

GPIO1/3 remain available to the carrier's USB-UART bridge. GPIO2 is not used for OE because it affects serial boot. GPIO5 is no longer used for diagnostics.

## Raspberry Pi connections

J9: pins 1–2 are 5.1 V, pins 3–4 ground. Never connect J9 power and Pi USB-C power simultaneously without a proper ORing design.

J10 is 1x8, 2.54 mm:

1. GND
2. GND
3. Pi GPIO14/TX, physical pin 8, to ESP GPIO18
4. ESP GPIO19 to Pi GPIO15/RX, physical pin 10
5. Pi GPIO17, physical pin 11, servo-power enable
6. motor diagnostic to Pi GPIO27, physical pin 13
7. optional Pi GPIO2/SDA, physical pin 3, through DNP link
8. optional Pi GPIO3/SCL, physical pin 5, through DNP link

Pi 5 UART requires `dtoverlay=uart0-pi5` and the serial console must be disabled. Direct GPIO-header power may require Raspberry Pi power configuration before high-current USB peripherals are allowed.

## Motor harness

J4/J5 order is fixed from the supplied harness:

1. red motor OUTA
2. black encoder ground
3. yellow encoder A
4. green encoder B
5. blue filtered/protected encoder 3.3 V
6. white motor OUTB

J15/J16 large pads are the primary motor-power connection. JST-PH motor pins 1/6 are isolated by normally-open solder jumpers; bridge those jumpers only for low-current bench operation. C18/C19 are fitted physically at the motor terminals and excluded from the PCB.

## Servo behavior

PCA9685 channels LED0/1/2 independently command J12/J13/J14. All share a 50 Hz frame but have independent pulse widths. Normal hobby servo wiring provides no position feedback to the ESP32; the servo's internal potentiometer/encoder is used only by its internal controller.

U13/U14/U15 are SN74AHCT1G125 buffers powered by the 4.85 V wrist rail. They accept 3.3 V PCA9685 outputs and produce 4.85 V PWM for the Miuzei, MG996R, and MG90S. Their OE pins share the PCA9685 active-low OE signal, and removing servo power also removes buffer power.

## Firmware safety requirements

- Start all wheel PWM/INA/INB low.
- Keep servo OE disabled and `SERVO_POWER_ENABLE` low until communications and limits are valid.
- Calibrate both VNH5019 current-sense channels.
- Implement a fast motor overcurrent/stall timer; 5 A blade fuses protect wiring, not the small motors.
- Stop motion on motor diagnostic, encoder timeout, low battery, lost Pi heartbeat, or E-stop state inferred/monitored by the final safety hardware.
- Use bounded retries and require a deliberate re-arm after a serious overcurrent or E-stop.

## Current project files

- KiCad project: `pickleball_robot_controller.kicad_pro`
- Generator/source of truth: `generate_kicad_multisheet.py`
- Full pin/layout guide: `SCHEMATIC_GUIDE.md`
- Pre-manufacture gates: `DESIGN_REVIEW.md`
- Ordering notes: `ORDERING_GUIDE.md`
- Exported BOM/PDF/ERC files are regenerated from the KiCad project.
