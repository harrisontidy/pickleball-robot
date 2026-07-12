# Pickleball Robot Controller — Discrete-Component Schematic Guide

Revision target: controller PCB R1, KiCad 10

This design uses component ICs and passives on the custom PCB. The ESP32-PICO-KIT V4.1 remains a removable controller board because it is hardware already owned. There are no plug-in buck or motor-driver modules.

## Design ratings

- Battery: 3S LiPo, 9–12.6 V operating range, XT60.
- Wheel motors: two 12 V GA25-370 motors.
- Provisional stall current: 5 A each, 10 A combined.
- Main fuse: external 15 A automotive blade fuse close to battery.
- Motor driver PWM: 15–20 kHz.
- Logic rail: regulated 5 V; ESP32 board creates its own 3.3 V rail.

## Sheet 1 — Battery input and protection

### Parts

| Ref | Part/value | Package | Purpose |
|---|---|---|---|
| J1 | XT60PW-M PCB connector, or 2-pin 5.08 mm terminal for an XT60 pigtail | through-hole | battery input |
| F1 | 15 A automotive blade fuse | external inline holder | protects battery wiring |
| SW1 | latching emergency-stop controlling a suitably rated external disconnect | external | physically removes actuator power |
| D1 | SMBJ18A | SMB/DO-214AA | motor-rail transient clamp |
| C1 | 1000 µF, 25 V, low-ESR | radial through-hole | main bulk capacitor |
| C2 | 1 µF, 25 V, X7R | 1206 | high-frequency bulk bypass |
| C3 | 100 nF, 25–50 V, X7R | 0805 | high-frequency bypass |
| R1 | 100 kΩ, 1% | 0805 | battery monitor upper divider |
| R2 | 27 kΩ, 1% | 0805 | battery monitor lower divider |
| R3 | 1 kΩ | 0805 | ESP32 ADC protection |
| C4 | 100 nF | 0805 | battery ADC filter |
| D2 | BAT54S | SOT-23 | ADC clamp to 3V3/GND |

### Connections

```text
J1.1 BAT+ -> external F1 -> external E-stop/disconnect -> VBAT_SW
J1.2 BAT- ------------------------------------------------> GND

D1 cathode -> VBAT_SW
D1 anode   -> GND
C1 positive -> VBAT_SW; C1 negative -> GND
C2/C3 -> between VBAT_SW and GND

VBAT_SW -> R1 100k -> BAT_SENSE_RAW -> R2 27k -> GND
BAT_SENSE_RAW -> C4 100nF -> GND
BAT_SENSE_RAW -> R3 1k -> BAT_ADC -> ESP32 GPIO33
D2 clamps BAT_ADC to 3V3 and GND
```

At 12.6 V the divider produces about 2.68 V. In firmware, stop drive operation around 10.2 V under light load and also check individual cells with the balance connector during charging/maintenance.

## Sheet 2 — 5 V buck converter

Use an **LM2596S-5.0 fixed-output regulator IC**, not an LM2596 module. This rail powers the ESP32 carrier and low-current logic only.

### Parts

| Ref | Part/value | Package | Purpose |
|---|---|---|---|
| U1 | LM2596S-5.0/NOPB | TO-263-5/D2PAK | 5 V buck regulator |
| L1 | 33 µH shielded power inductor, ≥4 A saturation, low DCR | e.g. Bourns SRP1265A-330M | buck inductor |
| D3 | SS54 or equivalent 5 A, 40 V Schottky | SMA/SMB | catch diode |
| C5 | 220 µF, 25 V, low-ESR | radial | input capacitor |
| C6 | 100 nF, 25 V | 0805 | input ceramic |
| C7 | 330 µF, 10 V, low-ESR | radial | output capacitor |
| C8 | 22 µF, 10 V, X7R | 1210 | output ceramic |
| R4 | 100 kΩ | 0805 | ON/OFF pull-down; keeps regulator enabled |
| TP1/TP2 | test points | through-hole/SMD | 5V and GND |

### Connections

```text
U1 VIN     -> VBAT_SW
U1 GND/tab -> GND copper area
U1 ON/OFF  -> GND through R4
U1 SW      -> SW_NODE
D3 cathode -> SW_NODE
D3 anode   -> GND
L1         -> SW_NODE on one end, +5V on the other
C5/C6      -> VBAT_SW to GND, immediately beside U1
C7/C8      -> +5V to GND, immediately beside L1/output return
U1 FB      -> +5V after L1
```

Keep SW_NODE extremely small. Do not run it under the ESP32 antenna or encoder traces.

## Sheet 3 — ESP32-PICO-KIT V4.1 carrier

Use two 1x17, 2.54 mm female socket strips. Verify row spacing with calipers before placing footprints. The official schematic labels the populated pins as positions 4–20 of each 20-pin connector; the three antenna-end flash pads are not installed into the carrier sockets.

### Supporting parts

| Ref | Part/value | Package |
|---|---|---|
| J2/J3 | 1x17 female socket headers, 2.54 mm | through-hole |
| C9 | 470 µF, 10 V | radial |
| C10/C11 | 100 nF | 0805 |
| R5 | 10 kΩ | 0805 |
| LED1 | green LED | 0805 |
| R6 | 1 kΩ | 0805 |

### Connections

```text
+5V -> ESP32 EXT_5V pin
GND -> both available ESP32 GND pins
C9/C10 -> +5V to GND near socket
3V3 -> C11 to GND and logic pull-ups only
3V3 -> R6 -> LED1 anode; LED1 cathode -> GND (optional power indicator)
```

Never power the ESP32 through Micro-USB and EXT_5V simultaneously. Keep all copper and components away from the antenna end.

## Raspberry Pi 5 connections

The PCB provides two physically separate Pi interfaces:

1. **J8/J9 high-current power pass-through.** J8 accepts regulated 5 V from a separate 5 V/5 A supply. J9 is a four-contact Mini-Fit Jr output with two parallel 5 V contacts and two parallel ground contacts. The LM2596 control regulator must never power the Pi.
2. **J10 low-current UART/control connector.** Use an 8-pin JST-XH connector: `3V3 reference`, `GND`, `PI_TX`, `PI_RX`, `PI_ENABLE`, `CTRL_FAULT`, `I2C_SDA`, `I2C_SCL`.

UART wiring:

```text
Raspberry Pi GPIO14 / TXD -> 1k series -> ESP32 GPIO3 / RXD0
ESP32 GPIO1 / TXD0 -> 1k series -> Raspberry Pi GPIO15 / RXD
Pi GND -------------------------------> controller GND
```

Both boards use 3.3 V UART logic, so no level shifter is required. Do not connect the two 3.3 V rails together as power sources; the J10 3V3 pin is a reference/identification pin and should be fitted through a 1 kΩ resistor or left unconnected until the final cable direction is chosen. The ESP32 USB-UART bridge also uses RXD0/TXD0, so do not actively drive the Pi UART and Micro-USB serial adapter at the same time.

The optional I2C pins are included for future expansion, but UART is the recommended first Pi-to-ESP32 link.

## Sheets 4 and 5 — left/right VNH5019 motor channels

Duplicate this entire circuit once for each motor. Use U2 for left and U3 for right.

### Parts per motor

| Ref group | Part/value | Package | Purpose |
|---|---|---|---|
| U2/U3 | VNH5019A-E | MultiPowerSO-30 | complete protected H-bridge IC |
| C12/C15 | 470 µF, 25 V, low-ESR | radial | local motor bulk |
| C13/C16 | 100 nF, 25–50 V | 0805 | local supply bypass |
| R7/R14 | 1 kΩ, 1% | 0805 | current-sense load |
| C14/C17 | 10 nF | 0805 | current-sense filter |
| R8–R10 / R15–R17 | 100 kΩ | 0805 | INA, INB, PWM pull-downs |
| R11/R18 | 10 kΩ | 0805 | diagnostic pull-up |
| R12/R13 / R19/R20 | 1 kΩ | 0805 | protection between diagnostic pins and shared FAULT net |
| J4/J5 | 2-pin 5.08 mm terminal, ≥10 A rated | through-hole | motor connection |
| C_MOTOR | 100 nF, ≥50 V ceramic | solder directly at motor terminals | brush-noise suppression |

### Power/output connections

Use the VNH5019 datasheet pin names, not guessed package numbers:

```text
all VCC pins/pads -> VBAT_SW with a wide copper pour
all GND pins/pads -> power ground plane with thermal vias
OUTA pins/pad -> motor connector terminal 1
OUTB pins/pad -> motor connector terminal 2
Cbulk 470uF and 100nF -> VCC to GND immediately beside the IC
CS_DIS -> GND (current sensing enabled)
CS -> 1k to GND and -> 10nF to GND and -> ESP32 ADC input
```

### Control/diagnostic connections

```text
INA -> ESP32 output; add 100k pull-down to GND
INB -> ESP32 output; add 100k pull-down to GND
PWM -> ESP32 PWM output; add 100k pull-down to GND
ENA/DIAGA -> 1k -> FAULT; 10k pull-up from FAULT to 3V3
ENB/DIAGB -> 1k -> same FAULT net
```

The IC accepts 3 V CMOS inputs. A low PWM disables drive. Firmware must start with PWM low.

### ESP32 assignments

| Function | GPIO |
|---|---:|
| LEFT_PWM | 25 |
| LEFT_INA | 26 |
| LEFT_INB | 27 |
| RIGHT_PWM | 14 |
| RIGHT_INA | 18 |
| RIGHT_INB | 19 |
| LEFT_FAULT | 32 |
| BAT_ADC | 33 |
| LEFT_CURRENT | 36 / SENSOR_VP |
| RIGHT_CURRENT | 39 / SENSOR_VN |

If a separate RIGHT_FAULT input is desired, use GPIO23. GPIO34/35 are reserved below for encoder signals.

## Sheet 6 — encoder inputs

Power both motor encoders from 3.3 V so level shifting is unnecessary. Buffer all four signals through a 3.3 V Schmitt-trigger IC.

### Parts

| Ref | Part/value | Package |
|---|---|---|
| U4 | SN74LVC14APW hex Schmitt inverter | TSSOP-14 |
| J6/J7 | JST-XH 1x4 vertical headers | through-hole |
| R21–R24 | 1 kΩ series | 0805 |
| R25–R28 | 10 kΩ pull-up to 3V3 | 0805 |
| C18–C21 | 1 nF | 0805 |
| C22 | 100 nF decoupling | 0805 |

### Connections

Each connector is `3V3, GND, ENCA, ENCB`.

```text
encoder signal -> 1k series -> FILTER_NODE -> one U4 input
FILTER_NODE -> 10k -> 3V3
FILTER_NODE -> 1nF -> GND
U4 output -> ESP32 GPIO
U4 VCC -> 3V3; U4 GND -> GND; 100nF directly at U4
unused U4 inputs -> GND; unused outputs -> no connection
```

Assignments:

| Encoder | GPIO |
|---|---:|
| Left A | 34 |
| Left B | 35 |
| Right A | 37 |
| Right B | 38 |

The inverter changes signal polarity but not encoder counts or direction as long as both channels of a motor pass through identical inverter stages.

## Minimum consolidated BOM

| Qty | Part |
|---:|---|
| 1 | LM2596S-5.0/NOPB |
| 1 | 33 µH ≥4 A shielded inductor |
| 1 | SS54 Schottky diode |
| 2 | VNH5019A-E motor-driver IC |
| 1 | SN74LVC14APW Schmitt buffer |
| 1 | SMBJ18A TVS diode |
| 1 | BAT54S dual Schottky |
| 1 | XT60PW-M or XT60 pigtail plus terminal block |
| 2 | 2-pin ≥10 A motor terminal blocks |
| 2 | JST-XH 1x4 encoder headers |
| 2 | 1x17 2.54 mm female ESP32 socket strips |
| 1 | 1000 µF 25 V low-ESR capacitor |
| 2 | 470 µF 25 V low-ESR capacitors for drivers |
| 1 | 470 µF 10 V capacitor for ESP32 rail |
| 1 | 330 µF 10 V low-ESR buck output capacitor |
| 1 | 220 µF 25 V buck input capacitor |
| assorted | listed 0805/1206/1210 resistors and ceramic capacitors |
| external | 15 A blade fuse/holder, latching E-stop/disconnect, genuine 3S balance charger |

## PCB rules that are part of the electrical design

- Use a 4-layer PCB if possible: top components/high current, solid GND plane, power/signals, bottom copper/thermal spreading.
- Use 2 oz outer copper if affordable.
- Use copper pours, not ordinary signal tracks, for VBAT, GND, OUTA, and OUTB.
- Put many small thermal vias under each VNH5019 exposed pad exactly as ST recommends; do not use thermal reliefs on power pads.
- Keep logic and encoder connectors away from motor outputs and the buck switch node.
- Route each motor pair together and keep it away from encoder cables.
- Put bulk capacitors beside the drivers, not beside the battery connector.
- Do not place copper under or immediately in front of the ESP32 antenna.
- The VNH5019 is not realistically hand-solderable with only a normal iron. Use solder paste and a hot plate/reflow oven or hot air, and inspect for bridges.

## Bring-up sequence

1. Assemble only input protection and the 5 V buck; test from a current-limited bench supply at 9, 11.1, and 12.6 V.
2. Verify 5 V before inserting the ESP32.
3. Insert/program ESP32 and verify encoder inputs using hand rotation only.
4. Assemble one VNH5019 channel and test with a small fuse and one unloaded motor.
5. Confirm direction, braking, current sense, and fault response.
6. Assemble the second channel.
7. Test from the LiPo only after the bench tests pass and the external 15 A fuse/E-stop are installed.
