# Pickleball Robot — Project Memory and Electrical Plan

Updated: 2026-07-12

This file is the durable project reference. Update it whenever a part or design choice changes.

## Project goal

Build a mobile robotic pickleball player that sees an incoming ball, moves into position, and physically swings a real paddle. This is not a ball launcher.

## Confirmed / supplied hardware

- Raspberry Pi 5 for vision, tracking, trajectory prediction, and high-level planning.
- Hailo-8L accelerator for a compact YOLO pickleball detector.
- USB webcam initially; a faster CSI or global-shutter camera may come later.
- 2020 aluminum-extrusion mobile chassis with printed wheel/hub parts.
- Two Huyuduo GA25-370 brushed gearmotors, 12 V, 500 RPM, with two-channel encoders (Amazon screenshot supplied 2026-07-12).
- Espressif ESP32-PICO-KIT V4.1, visually confirmed from front/back photographs on 2026-07-12. The board has two 20-position edge rows, with 17 populated header positions and three flash pads at the antenna end on each side.
- Current battery: AMZZN 3S LiPo, 11.1 V nominal, 2000 mAh, advertised 35C, XT60 discharge connector, 4-pin balance connector, and supplied USB charging cable.
- Planned arm prototype: 25 kg·cm-class 270° servo for main swing; MG996R-class elbow; initially fixed wrist, later MG90S if useful.

## Wheel-motor wire map from the supplied listing image

| Wire | Function |
|---|---|
| Red | Motor terminal A |
| White | Motor terminal B |
| Blue | Encoder supply positive, 3.3–5 V |
| Black | Encoder ground |
| Yellow | Encoder channel A |
| Green | Encoder channel B |

Reversing red and white reverses motor direction. Never connect encoder power backward. Verify the colors with a current-limited bench supply before final harness assembly because marketplace motor batches can vary.

The exact motor stall current is **not confirmed** by the Amazon screenshot. Similar GA25-370 variants vary substantially. For the first schematic, assume **5 A maximum stall current per motor, 10 A combined**. This is deliberately conservative and is not a measured specification. Measure each actual motor's locked-rotor current very briefly at 12 V with a current-limited supply before production hardware or a later PCB revision.

## Recommended first electrical architecture

The custom PCB contains the wheel H-bridge ICs, logic regulator, ESP32 carrier, sensing, and two wheel-motor H-bridge ICs. Servo power and Pi/Hailo power remain separate because their requirements are different and not yet finalized.

```text
BATTERY CONNECTOR (XT60)
        |
   MAIN FUSE
        |
 LATCHING E-STOP / CONTACTOR
        |
  POWER DISTRIBUTION STAR
    |          |           |
    |          |           +--> servo UBEC --> arm servos
    |          +--> 5 V regulator --> Pi 5/Hailo (separate branch)
    +--> 12 V motor rail --> dual H-bridge --> left/right GA25-370
                         |
                         +--> ESP32 control: PWM + DIR per channel

Small 5 V logic regulator --> ESP32-PICO-KIT EXT_5V
ESP32 3.3 V -------------> encoder blue wires
ESP32 GND ----------------> encoder black wires / driver logic GND
Encoder A/B --------------> protected ESP32 GPIO inputs
```

All grounds share one reference, but motor current must return through heavy wiring to the star point rather than through the ESP32/encoder ground traces.

## Battery and the requested 12 V converter

Pick one of these paths:

### Selected path for the current prototype — 3S LiPo

- AMZZN 3S LiPo (12.6 V full, 11.1 V nominal, approximately 9.0–9.6 V near the safe lower limit depending on load and cell health).
- Feed the motor driver directly after the fuse/E-stop.
- No 12 V buck is used. Motor speed will fall somewhat as the battery discharges.
- Use a **15 A automotive blade fuse** as the provisional main actuator fuse. If it nuisance-blows during normal acceleration, measure current before increasing it; never just install a much larger fuse.
- Treat the advertised 35C/70 A capability as a marketing maximum, not a design current. The XT60 and LiPo can deliver dangerous fault current, so the fuse must be close to the battery connector.
- Add low-battery monitoring and stop motor operation when the pack reaches about **10.2 V under light load** (3.4 V/cell). Never continue until the pack is deeply discharged.
- The pictured battery has a balance connector. Use a reputable **3S balance charger in LiPo mode**, preferably with cell-voltage display and storage mode. Do not leave the supplied USB charger unattended, and do not charge the battery inside the robot.
- Charge/store in a LiPo-safe location or bag, inspect for swelling/damage, and disconnect it for storage.

### Possible later path — regulated 12 V rail

- 4S lithium pack (16.8 V full) with appropriate BMS.
- A **12 V high-current buck module** between the distribution point and motor driver.
- The buck must survive at least the combined measured motor startup/stall demand; do not buy it based only on an advertised peak rating.
- Prefer an enclosed or PCB module with screw terminals, current limiting, thermal shutdown, and a real datasheet. A cheap XL4016-style board is acceptable only for bench experiments after load testing; it is not yet approved for the moving robot.

No exact 12 V buck is frozen into the BOM until battery type and measured motor stall current are known. This prevents buying a module that is inherently undersized.

## Recommended wheel driver

The user clarified that the custom PCB should use component ICs and passives rather than motor-driver or regulator modules. Revision 1 therefore uses **two VNH5019A-E full-bridge ICs**, one per motor. Each accepts 3 V logic and integrates the H-bridge MOSFETs, protection, diagnostics, and current sensing. See `SCHEMATIC_GUIDE.md` for the complete connections and BOM.

Provisional ESP32 signals:

| Signal | ESP32 GPIO | Notes |
|---|---:|---|
| LEFT_PWM | 25 | PWM-capable output |
| LEFT_DIR | 26 | digital output |
| RIGHT_PWM | 27 | PWM-capable output |
| RIGHT_DIR | 14 | digital output |
| LEFT_ENC_A | 34 | input only; add pull-up/filter |
| LEFT_ENC_B | 35 | input only; add pull-up/filter |
| RIGHT_ENC_A | 36 | input only; add pull-up/filter |
| RIGHT_ENC_B | 39 | input only; add pull-up/filter |
| I2C_SDA | 21 | PCA9685 / expansion |
| I2C_SCL | 22 | PCA9685 / expansion |

Avoid GPIO 0, 2, 5, 12, and 15 for external devices that could force the wrong boot state. Confirm this pin map against the physical board and firmware before routing.

## ESP32-PICO-KIT V4.1 carrier circuit

Mount the complete development kit in two 1x17, 2.54 mm female socket headers; do not recreate its ESP32, USB-UART, antenna, LDO, boot, and reset circuits on revision 1. The supplied photos confirm the exact V4.1 board. Leave the antenna end and its six flash pads unobstructed and keep copper, battery wiring, motors, and metal chassis parts away from the antenna area.

- Power it from the PCB's LM2596S-5.0 regulator circuit connected to `EXT_5V` and GND.
- Do not power through USB and EXT_5V simultaneously.
- Put 470 µF electrolytic plus 100 nF ceramic near the carrier's 5 V input.
- Add a 2-pin 5.08 mm terminal block for logic 5 V input if the regulator is off-board.
- Add labeled test points: 5V, 3V3, GND, each PWM/DIR signal, and each encoder channel.
- Add 10 kΩ pull-ups to 3.3 V on encoder signals only if the actual encoder outputs are open collector. Populate as DNP until verified.
- Add optional input conditioning per encoder channel: 1 kΩ series resistor, 10 nF to GND after the resistor, and a 3.3 V ESD clamp/array near the connector.

## Solder-friendly connectors and parts

| Ref/use | Recommended style | Rating / note |
|---|---|---|
| Battery | Genuine XT60 panel/pigtail | keyed, high-current; use 12–14 AWG depending on measured current |
| Main actuator fuse | Inline automotive blade holder | 15 A provisional, mounted close to battery XT60 positive |
| E-stop | Latching mushroom switch controlling a DC contactor/high-current disconnect | E-stop must remove actuator power, not merely send a GPIO command |
| PCB power | 5.08 mm pluggable terminal blocks | choose genuine parts rated above circuit current |
| Motor output | 2-pin 5.08 mm pluggable terminal per motor | 16–18 AWG provisional |
| Encoder | JST-XH 1x4 per motor | 3.3V, GND, A, B; low current only |
| Driver control | JST-XH 1x6 | 3.3V logic reference, GND, LPWM, LDIR, RPWM, RDIR |
| ESP32 sockets | 2x 1x17 female headers, 2.54 mm | verify board spacing physically before PCB order |
| Bulk capacitor at driver | 1000 µF, 25 V, low-ESR electrolytic + 1 µF film/ceramic | place at driver supply input; follow driver manual if it specifies more |
| Motor suppression | 100 nF ceramic, preferably ≥50 V, directly across each motor's red/white terminals | keep leads extremely short |
| Logic regulator | LM2596S-5.0/NOPB plus external diode, 33 µH inductor, and capacitors | PCB-level buck circuit; powers only ESP32/control logic, not Pi or servos |

## Pi 5 / Hailo power

Give the Pi/Hailo its own high-quality 5 V, 5 A branch. The Pi 5 expects a strong 5 V supply and can restrict peripherals on a 3 A supply. For the prototype, the least troublesome option is a dedicated automotive/robotics 5 V regulator feeding a proper USB-C power-input cable/module. Do not route Pi power through the first custom control PCB.

## Arm power

Use a separate 6–7.4 V high-current UBEC/regulator for servos. Budget roughly 2–3 A peak for each standard high-torque servo and keep servo current out of the ESP32 board. The PCA9685 controls signals only; its logic VCC is not the servo power rail.

## Before drawing/finalizing the KiCad schematic

1. Measure the exact ESP32 header-row spacing and pin pitch with calipers before ordering the carrier PCB; the photos confirm identity but not a manufacturing-tolerance-safe footprint.
2. Obtain/use a reputable 3S balance charger and confirm the battery's individual cell voltages before use.
3. Measure one motor's no-load current and very brief stall current at 12 V; repeat for the other motor. Until then use the 5 A-per-motor design assumption.
4. Confirm the encoder output voltage and type with a meter/oscilloscope at 3.3 V supply.
5. State wheel diameter, robot mass, target top speed, and whether there are two or four driven motors.
6. Assemble and bench-test one VNH5019 channel with one motor, fuse, E-stop, and current-limited supply before populating the second channel.

## Current design status

- Architecture: established.
- Wheel motor model/wiring: identified from supplied image.
- Exact motor current: unknown; provisional schematic value is 5 A stall per motor / 10 A combined.
- Battery: AMZZN 3S 11.1 V 2000 mAh LiPo with XT60, advertised 35C.
- 12 V regulator: not required for the current 3S battery and wheel-motor branch.
- Driver: two PCB-mounted VNH5019A-E full-bridge ICs, one per wheel motor.
- ESP32 board: Espressif ESP32-PICO-KIT V4.1 visually confirmed from supplied photographs.
- Custom PCB revision 1: ESP32 carrier, PCB-level 5 V buck, encoder conditioning, sensing, and two PCB-mounted VNH5019 wheel drivers. Servo and Pi/Hailo power remain separate.

## Generated KiCad project

The current clean project is `pickleball_robot_controller.kicad_pro` / `pickleball_robot_controller.kicad_sch` (KiCad 10). It includes battery protection, two wheel drivers, encoder conditioning, ESP32 carrier, Raspberry Pi UART/control and separate 5 V/5 A power pass-through, PCA9685 servo control, and three 6 V servo outputs for the 25 kg main swing servo, MG996R elbow, and MG90S wrist. KiCad CLI ERC reports zero violations as of 2026-07-12. The custom ESP32 carrier footprint is in `PickleballRobot.pretty`; its assumed 17.78 mm row spacing must still be checked against the physical board with calipers before fabrication.
