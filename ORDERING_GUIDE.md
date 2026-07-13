# Ordering guide — R2-MULTISHEET

The generated `pickleball_robot_controller-bom.csv` is the complete reference/value/footprint list. This file records the important exact selections and the parts that still require a purchasing decision.

## Core ICs

| Refs | Recommended part | Notes |
|---|---|---|
| U1 | LM2596S-5.0/NOPB | 5 V logic buck, TO-263-5 |
| U2, U3 | ST VNH5019A-E | MultiPowerSO-30, hot-air/reflow and thermal-via footprint |
| U4, U10, U11 | TI TPS54560BDDA | 5 A asynchronous buck, DDA PowerPAD-8 |
| U5 | NXP PCA9685PW,118 | 16-channel PWM controller, TSSOP-28 |
| U6–U9 | TI SN74LVC1G14DBVR | single Schmitt inverter, SOT-23-5 |
| U12 | Analog Devices LTC4365ITS8#TRPBF | whole-board UV/OV and reverse-supply controller, TSOT-23-8 |
| U13–U15 | TI SN74AHCT1G125DBVR | guaranteed 3.3 V-to-4.85 V servo PWM buffers, SOT-23-5 |
| U16 | Analog Devices LT1963AEQ#PBF | 1.5 A adjustable LDO, TO-263-5; 4.85 V MG90S rail |

## High-current power parts

| Refs | Recommended part / class |
|---|---|
| L2–L4 | Coilcraft XAL7070-682MEC, 6.8 µH |
| D9–D11 | Diodes Inc. B560C-13-F, 5 A / 60 V Schottky |
| C1 | Panasonic EEU-FR1V102, 1000 µF / 35 V, 12.5 mm radial |
| C12/C15 | Panasonic EEU-FR1V471, 470 µF / 35 V, 10 mm radial |
| C5/C7 | Panasonic EEU-FR1E221 / EEU-FR1A331; LM2596-qualified input/output electrolytics |
| F2–F6 holder | Keystone 3568 mini-blade PCB holder |
| F7/F8 | Bourns MF-PSMF010X-2, 100 mA hold resettable fuse, 0805 |
| F9 | Bourns MF-MSMF150/16X, 1.5 A hold resettable fuse, 1812 |
| F2–F6 fuse | start with 5 A automotive mini blade; revise only after measured current/thermal testing |
| F1 | 15 A ATO blade at the battery input |
| Q5/Q6 | Infineon IRLB4030PBF, 100 V logic-level N-MOSFET, TO-220; provide thermal copper and clearance |
| D1, D21 | SMBJ15CA bidirectional TVS |
| J1 | AMASS XT60PW-M board-mount male connector |
| J18 | Phoenix Contact MKDS 3/2-5.08 (24 A, up to 12 AWG), external relay-contact loop |
| J21 | Phoenix Contact MKDS-1,5/2-5.08, low-current E-stop relay-coil supply |
| J9 | Molex 39-30-1040 right-angle 2x2 Mini-Fit Jr header; use its exact drawing before PCB order |
| J4/J5 | JST B6B-PH-K-S(LF)(SN), 2.00 mm six-pin vertical header |

U4 uses three Murata `GRM32ER71A476KE15L` 47 µF/10 V X7R 1210 capacitors. U10/U11 use four Samsung `CL32B226KLV6PN#` 22 µF/35 V X7R 1210 capacitors per rail. TPS inputs use four `GRM21BR71E225KA73L` 2.2 µF/25 V X7R 0805 capacitors per converter. Confirm DC-bias curves; do not substitute nominal capacitance without rechecking compensation.

All ordinary resistors and small capacitors are 0805. Exceptions are intentional: high-capacitance output MLCCs are 1210, TVSs/Schottkys use power packages, bulk capacitors and fuse holders are through-hole, and the high-current ICs have exposed pads.

## Connector mating parts

- J9: mating 4-circuit Mini-Fit Jr receptacle, properly rated crimp terminals, two 5 V wires and two ground wires.
- J10/J12/J13/J14/J20: ordinary 2.54 mm female housings or Dupont leads, but use locking housings in the moving robot where possible.
- J4/J5: JST PHR-6 housing with SPH-002T-P0.5S contacts, subject to confirmation against the motor's actual plug.
- J11/J17: 5.00 mm terminal blocks matching the assigned footprint.
- E-stop: Schneider XB5AS8442 1NC positive-opening turn-release button plus Panasonic CB1aF-RM-12V-A-5 12 V relay with internal resistor suppression; wire its NO contact across J18.

## Do not order yet without checking

- Exact electrolytic series, diameter, height, ESR, ripple current, and lead spacing.
- U11 output MLCC DC-bias curve and availability for Samsung `CL32B226KLV6PN#`.
- Servo connector polarity and exact purchased SKU.
- Motor JST family by direct measurement/continuity test.
- Fuse nuisance-blow behavior after real motor/servo testing.
- Q5/Q6 thermal performance at worst-case continuous board current.

Buy at least two spare U2/U3 and U4/U10/U11 parts for prototype rework. The exposed-pad packages require paste plus hot air/hot plate/reflow; an iron alone cannot reliably solder the center pads.
