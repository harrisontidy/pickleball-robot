# Pickleball robot controller schematic guide

This guide describes revision **R2-MULTISHEET**. The source of truth is `generate_kicad_multisheet.py`; the generated KiCad project is `pickleball_robot_controller.kicad_pro`.

## Sheet map

1. `01_power_and_pi.kicad_sch` — 3S battery input, main protection, real E-stop loop, battery ADC, 5 V logic supply, and 5.1 V Raspberry Pi supply.
2. `02_esp32_and_pi.kicad_sch` — ESP32-PICO-KIT V4.1 carrier, Pi UART/control header, fault aggregation, optional I2C links, status LEDs, and debug points.
3. `03_left_motor.kicad_sch` — left VNH5019 driver, branch fuse, current-sense protection, motor/encoder connector, and large motor-wire pads.
4. `04_right_motor.kicad_sch` — right channel, matching sheet 3.
5. `05_encoder_inputs.kicad_sch` — filtered encoder 3.3 V rail, cable resistors, four Schmitt buffers, local bypass capacitors, and test points.
6. `06_arm_servos.kicad_sch` — 6 V servo buck, PCA9685, and three independent PWM outputs.
7. `07_main_servo_8v4.kicad_sch` — dedicated 8.4 V rail for the Miuzei main-swing servo.

J1 uses the KiCad AMASS XT60PW-M footprint's actual polarity: pin 1 is negative/GND and pin 2 is positive/BAT_RAW. Do not reverse these to match a generic two-pin connector convention.

## Canonical ESP32 pin map

| Function | ESP32 GPIO |
|---|---:|
| PCA9685 SDA / SCL | 21 / 22 |
| Raspberry Pi UART RX / TX | 18 / 19 |
| Aggregated motor fault | 23 |
| Servo PWM output-enable | 32 |
| Left PWM / INA / INB | 25 / 26 / 27 |
| Right PWM / INA / INB | 14 / 13 / 4 |
| Battery ADC | 33 |
| Left / right current ADC | 36 / 39 |
| Left encoder A / B | 34 / 35 |
| Right encoder A / B | 37 / 38 |

GPIO2 is no longer used for servo OE, GPIO5 is deliberately unused, and UART0 GPIO1/3 remains free for the board's USB programming bridge.

## Raspberry Pi headers

J9 is the high-current Pi power connector: pins 1–2 are `PI_5V`, pins 3–4 are ground. It is a Molex Mini-Fit Jr 2x2 right-angle header. The Pi must not be powered from USB-C at the same time.

J10 is a normal 1x8 2.54 mm header:

| J10 | Signal | Raspberry Pi connection |
|---:|---|---|
| 1 | GND | any Pi ground |
| 2 | GND | second return wire |
| 3 | Pi TX to ESP GPIO18 | GPIO14, physical pin 8 |
| 4 | ESP GPIO19 to Pi RX | GPIO15, physical pin 10 |
| 5 | `SERVO_POWER_ENABLE` | GPIO17, physical pin 11 |
| 6 | aggregated motor fault | GPIO27, physical pin 13 |
| 7 | optional I2C SDA | GPIO2, physical pin 3; DNP R43 must be fitted |
| 8 | optional I2C SCL | GPIO3, physical pin 5; DNP R44 must be fitted |

J20 is a DNP bench override connected through R46 4.7 kΩ, so it cannot hard-short a Pi GPIO driven low. Leave it unpopulated for normal Pi control.

On Raspberry Pi 5, enable the primary UART with `dtoverlay=uart0-pi5` and disable the Linux serial console before using J10. Never assume the Pi 5 UART mapping matches older Pi models.

## Wheel-motor connections

J4 and J5 are JST-PH 2.00 mm six-pin headers matching the photographed cable order:

| Pin | Wire | Function |
|---:|---|---|
| 1 | red | motor OUTA |
| 2 | black | encoder ground |
| 3 | yellow | encoder A |
| 4 | green | encoder B |
| 5 | blue | filtered encoder 3.3 V |
| 6 | white | motor OUTB |

J15/J16 are the primary 1.7 mm through-hole motor-power pads. JST-PH motor pins 1/6 are isolated by normally-open JP1–JP4 solder jumpers. Leave the jumpers open with heavy motor wires; bridge them only for low-current bench tests. Fit external C18/C19 directly across each motor's red/white terminals.

Each driver has a 5 A mini-blade branch fuse, 10 kΩ safe-state pull-downs, 1 kΩ control resistors, separate diagnostics, 35 V local bulk plus ceramic bypass, and a protected current ADC. The VNH5019 custom footprint keeps exposed pads 31, 32, and 33 electrically separate and gives each its own windowed paste and thermal-via field.

## Servo system

U5 is a PCA9685. LED0, LED1, and LED2 generate independent commands; all three share a 50 Hz frame rate but can have different pulse widths.

| Header | Servo | Power | Pin order |
|---|---|---:|---|
| J12 | Miuzei 25KG 270° main swing | 8.4 V | 1 GND, 2 power, 3 PWM |
| J13 | MG996R elbow | 6 V | 1 GND, 2 power, 3 PWM |
| J14 | MG90S wrist | 6 V | 1 GND, 2 power, 3 PWM |

These hobby servos contain an internal control loop and position sensor, but they do not return their measured position to the ESP32 through the normal three-wire connector.

`SERVO_POWER_ENABLE` defaults low and controls both servo-regulator EN pins. PCA9685 OE also defaults disabled. This gives two startup safeguards: no servo power until the Pi enables it, and no PWM until the ESP32 enables outputs.

## Power rails

- `VBAT_SW`: fused 3S battery supply for Pi and logic.
- `ACT_VBAT`: battery supply after the external latching E-stop loop, used by motors and both servo regulators.
- `+5V_CTRL`: ESP32 and logic only.
- `PI_5V`: approximately 5.1 V, up to 5 A design target.
- `SERVO_6V`: 6.0 V rail for J13/J14.
- `MAIN_SERVO_8V4`: 8.4 V rail for J12.
- `ENC_3V3`: ferrite-filtered encoder supply.

The TPS54560 networks use corrected feedback, EN, catch-diode, and compensation connections. C30/C40/C61 and the three RC snubbers are real KiCad DNP parts; do not populate optional bulk/snubber parts until loop and switch-node measurements justify them.

## PCB rules that are not optional

- Four-layer board strongly preferred: signal/power, solid ground, power distribution, signal/power.
- Use 2 oz outer copper if practical.
- Keep every buck input-capacitor/IC/diode loop extremely small; keep switch nodes away from ESP antenna, UART, ADC, and encoder traces.
- Use Kelvin feedback routing from the output-capacitor node.
- Put the ESP antenna beyond the board edge if possible. The footprint enforces F/B keepouts; also create matching inner-layer keepouts when the four-layer PCB is created.
- Use separate high-current actuator branches from a star point; do not route motor/servo return current through the logic ground path.
- Widen motor and rail copper with pours, not only traces. Verify current width using the board house's actual copper thickness and allowed temperature rise.
- Add mounting holes, motor-wire strain relief, connector pin-1 legends, fuse ratings, rail names, and polarity on silkscreen.
- Run ERC, PCB DRC, netlist comparison, Gerber inspection, drill inspection, and paste-window inspection before ordering.

## Known design gates before manufacture

1. Measure actual motor stall current or keep the conservative 5 A branch-fuse/copper allowance.
2. Confirm every physical connector and servo SKU against the purchased part.
3. Choose exact output MLCCs and verify their effective capacitance at 5.1 V, 6 V, and 8.4 V.
4. Add or purchase a genuine 3S low-voltage protection solution. The battery ADC and Pi-controlled enable are not a hardware LiPo cutoff.
5. Bench-test regulator startup and transient response on the first PCB with a current-limited supply and dummy loads.
6. Firmware must use calibrated current sense and a short overcurrent timeout. The 5 A motor fuses protect wiring, not the small motors.
