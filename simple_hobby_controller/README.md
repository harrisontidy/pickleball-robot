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
- XT60 3S battery input for the wheel driver.
- XT30 regulated 5 V input for the ESP32 and servos.
- One motor fuse, one motor bulk capacitor, one servo bulk capacitor, and the required local bypass parts.

There is no PCA9685, no on-board high-current buck converter, no level shifter, no BMS, no current-sense circuitry, and no extra status/test-point forest.

## Power wiring

1. Connect the 3S LiPo to J1 (XT60). This powers only the wheel H-bridge.
2. Use a battery Y lead to feed an external **regulated 5 V, 5-8 A RC UBEC**.
3. Connect the UBEC's regulated output to J2 (XT30). This powers the ESP32 carrier and all three servos.
4. Power the Raspberry Pi separately through a proper Pi 5 V supply or USB-C regulator. J11 does not power the Pi.

The amp rating is capacity, not forced current: a 5-8 A UBEC does not push 8 A into the servos. Each load draws only what it needs. The extra capacity prevents the ESP32 from resetting when a servo starts or is briefly loaded.

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
- Assign board rules: approximately 1.5-2.0 mm copper for battery/motor paths on 1 oz copper, 1.0-1.5 mm for the 5 V servo trunk, and 0.25 mm for logic signals. Use solid ground pours on both layers.
- Put J1-J4 and J8-J11 at board edges. Put C1 beside U1 and C3 beside the servo headers. Give U1 a large exposed-pad copper area with thermal vias.
- Run KiCad ERC again after any edit and DRC after routing.

The generated `simple-erc.json` currently reports **zero violations**.
