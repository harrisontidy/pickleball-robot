# Simple hobby controller

This is the recommended controller project. It deliberately replaces the earlier high-feature design with two readable schematic pages and one uncomplicated power plan.

Open `pickleball_robot_simple.kicad_pro` in KiCad 10. The project contains the schematic only; the PCB has not been routed yet.

## What is on the board

- ESP32-PICO-KIT V4.1 carrier.
- One DRV8848PWP dual H-bridge for both GA25-370 wheel motors.
- Two JST-PH 6-pin, 2.00 mm motor/encoder connectors.
- Two pairs of large solder pads for optional heavier motor wires.
- Three independent 5 V servo headers. Each has its own ESP32 PWM signal.
- One normal 2.54 mm Raspberry Pi UART header.
- One four-contact Micro-Fit Raspberry Pi power output on the shared 5 V rail.
- XT60 3S battery input for the wheel driver.
- On-board LM2678T-5.0 buck converter that makes the shared 5 V rail from the 3S battery.
- One motor fuse, one motor bulk capacitor, one servo bulk capacitor, and the required local bypass parts.

There is no PCA9685, no on-board high-current buck converter, no level shifter, no BMS, no current-sense circuitry, and no extra status/test-point forest.

## Power wiring

1. Connect the 3S LiPo to J1 (XT60). This powers only the wheel H-bridge.
2. The on-board LM2678T-5.0 buck converts the battery voltage to the single shared +5 V rail.
3. That rail powers the ESP32 carrier, all three servos, and Raspberry Pi power output J12.
4. Wire both J12 +5 V contacts to Raspberry Pi header pins 2 and 4. Wire both J12 ground contacts to two Pi ground pins, such as pins 6 and 9.

The fixed LM2678 buck is rated up to 5 A. That is enough for normal hobby testing, but it is not enough to guarantee a Raspberry Pi 5 plus three simultaneously stalled servos at maximum load. Each device draws only what it needs; if bench testing shows repeated 5 V brownouts, the simple fix is to power the Pi separately or change to a larger buck stage.

## Connector pinouts

Motor connectors J3 and J4 are JST PH B6B-PH-K, 2.00 mm pitch:

1. Red — motor terminal A
2. Black — encoder ground
3. Yellow — encoder A
4. Green — encoder B
5. Blue — encoder +3.3 V
6. White — motor terminal B

Servo connectors J8-J10:

1. Ground
2. Regulated +5 V
3. Independent PWM

Pi UART J11:

1. Ground
2. Pi TX to ESP32 GPIO18 RX
3. ESP32 GPIO19 TX to Pi RX
4. 3.3 V reference only; do not use it to power either computer

Pi power J12:

- Pins 1 and 2: shared regulated +5 V
- Pins 3 and 4: ground
- Use both contacts of each polarity so the current is shared between wires

## ESP32 signal map

| Function | ESP32 GPIO |
|---|---:|
| Main swing servo PWM | 25 |
| Elbow servo PWM | 26 |
| Wrist servo PWM | 27 |
| Left motor AIN1 / PWM-direction | 13 |
| Left motor AIN2 / PWM-direction | 4 |
| Right motor BIN1 / PWM-direction | 14 |
| Right motor BIN2 / PWM-direction | 23 |
| Left encoder A | 34 |
| Left encoder B | 35 |
| Right encoder A | 37 |
| Right encoder B | 38 |
| Pi TX to ESP32 UART RX | 18 |
| ESP32 UART TX to Pi RX | 19 |
| Motor-driver fault input | 22 |

## Important limits

- The DRV8848 operates from 4-18 V and has a 2 A peak protection threshold per bridge. It is a reasonable simple prototype choice, but the unknown wheel-motor stall current must be measured before ordering the PCB. If either motor needs more than roughly 1 A continuously or repeatedly trips the driver at startup, use a larger external motor driver instead of forcing this board to do it.
- The DRV8848 has a 0.65 mm-pitch exposed-pad package. It is the only fine-pitch part; solder paste plus hot air is recommended.
- The three servos are all intentionally powered at 5 V. This sacrifices some main-servo torque in exchange for one simple rail.
- A larger-capacity 3S battery is fine. A higher C rating is also fine. Do not change from 3S without redesigning the power plan.
- The PCB does not replace safe LiPo charging, storage, or low-voltage monitoring. Use a proper 3S balance charger and a battery alarm if the pack has no protected cutoff.

## Before making a PCB

- Confirm the physical JST connector keying and cable order against both motors.
- Measure motor stall current briefly with a current-limited bench supply.
- Confirm each servo behaves correctly at 5.0 V.
- Assign board rules: approximately 1.5-2.0 mm copper for battery/motor paths on 1 oz copper. Use a wide 5 V copper pour for the combined Pi/servo rail rather than a thin trace, and 0.25 mm traces for logic signals. Use solid ground pours on both layers.
- Put J1, J3-J4, J8-J12 at board edges. Follow the LM2678 datasheet layout closely: keep U2, D1, C1-C2, L1, and C7-C8 close together with a very small switching loop. Put C3 beside the servo/Pi branches. Give U1 a large exposed-pad copper area with thermal vias.
- Run KiCad ERC again after any edit and DRC after routing.

The generated `simple-erc.json` currently reports **zero violations**.
