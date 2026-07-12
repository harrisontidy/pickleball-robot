# Orderable, solderable controller parts

This is the build choice for the current schematic. Small passives are **0805**, not 1206. High-energy buck output capacitors are deliberately through-hole low-ESR parts; an 0805 capacitor cannot replace those.

## Parts requiring hot air / hot plate

| Refs | Exact part | Why |
|---|---|---|
| U4, U10, U11 | TI `TPS54560BDDA` | 5 A buck regulator, PowerPAD underside pad |
| U2, U3 | ST `VNH5019A-E` | wheel H-bridge, thermal pad |
| U5 | NXP `PCA9685PW,118` | TSSOP-28 servo PWM controller |
| L2, L3, L4 | Coilcraft `XAL7070-682MEC` | 6.8 uH shielded 7 mm power inductor |
| D9, D10, D11 | Diodes Inc. `B560C-13-F` | 60 V, 5 A Schottky buck diode, SMC package |

Use paste plus a heat gun/hot plate for U2/U3/U4/U10. The large exposed pads need good solder and thermal vias. Everything else below is practical with a normal iron and flux.

## Buck-regulator passives

| Refs | Exact part | Package / note |
|---|---|---|
| C32–C35, C46–C47 | Murata `GRM21BR71E225KA73L` | 2.2 uF, 25 V, X7R, 0805 |
| C31, C45 | Murata `GRM21BR71H104KA01L` | 100 nF, 50 V, X7R, 0805 |
| C38, C39, C50 | Nichicon `UPM1A221MHD` | 220 uF, 10 V, low-ESR radial; easy through-hole soldering |
| C44, C51 | Murata `GRM21BR61A105KA01L` | 1 uF, 10 V, X7R, 0805 |
| R30, R104 | Yageo `RC0805FR-07243KL` | 243 kΩ, 1%, 0805 |
| R31 | Yageo `RC0805FR-07442KL` | 442 kΩ, 1%, 0805 |
| R32, R106 | Yageo `RC0805FR-0790R9L` | 90.9 kΩ, 1%, 0805 |
| R105 | Yageo `RC0805FR-07590KL` | 590 kΩ, 1%, 0805 |
| R109 | Yageo `RC0805FR-07866KL` | 866 kΩ, 1%, 0805; sets the main-servo rail to about 8.42 V |
| R33, R107 | Yageo `RC0805FR-0710K2L` | 10.2 kΩ, 1%, 0805 |

## Connectors you plug into

| Refs | Exact part | What plugs in |
|---|---|---|
| J4, J5 | JST `B6B-PH-K-S(LF)(SN)` | your 6-wire GA25-370 motor/encoder cable; 2.00 mm pitch; order red/black/yellow/green/blue/white |
| J15, J16 | PCB solder pads from KiCad `SolderWire-1.5sqmm` footprint | 1.7 mm drill, 3.9 mm pad; separately solder the red/white motor-power wires here |
| J10 | Samtec `TSW-108-07-G-S` | eight-pin 2.54 mm male header; accepts ordinary female Dupont wires to the Pi |
| J12–J14 | Samtec `TSW-103-07-G-S` | ordinary 3-wire RC servo female plugs; 2.54 mm pitch |
| J9 | Molex `39-30-1040` | Pi 5 V power harness; use the matching Mini-Fit Jr housing/crimps |

Servo pin order is printed in the schematic as **GND / 6V / PWM**. Before plugging a servo in, confirm its black/brown wire aligns with `GND`, red with `6V`, and yellow/orange/white with `PWM`.

## Important buying rule

Do not substitute a smaller inductor, diode, or output capacitor in either TPS54560B circuit. TI's 5 V / 5 A reference design uses a 7.2 uH-class inductor and B560C-class diode; this design uses the nearby standard 6.8 uH Coilcraft part. The parts and layout determine whether the regulator stays cool and stable.
