# Core parts

| Ref | Qty | Part | Suggested exact part |
|---|---:|---|---|
| U1 | 1 | Dual H-bridge | Texas Instruments DRV8848PWP |
| J3, J4 | 2 | 6-pin motor connector, 2.00 mm | JST B6B-PH-K-S(LF)(SN) |
| J1 | 1 | Board XT60 | AMASS XT60PW-M |
| U2 | 1 | Fixed 5 V, 5 A buck regulator | Texas Instruments LM2678T-5.0/NOPB, TO-220-7 |
| D1 | 1 | Buck catch diode | SS54, 5 A 40 V Schottky, SMC package |
| L1 | 1 | Buck inductor | Bourns SRP1770TA-220M, 22 uH, high-current |
| C6 | 1 | Buck boost capacitor | 10 nF, 50 V, X7R, 0805 |
| C7, C8 | 2 | Buck output capacitors | 220 uF, 16 V, low-ESR radial |
| J7 | 1 | ESP32 carrier sockets | Two 1x17 2.54 mm female socket strips, 17.78 mm row spacing |
| J8-J10 | 3 | Servo header | 1x3 2.54 mm vertical breakaway header |
| J11 | 1 | Pi UART header | 1x4 2.54 mm vertical breakaway header |
| J12 | 1 | Pi 5 V power output | Molex Micro-Fit 3.0 43045-0415, 2x2 vertical; mating housing 43025-0400 |
| C1 | 1 | 470 uF, 25 V, low-ESR radial | Panasonic EEU-FR1E471 |
| C3 | 1 | 1000 uF, 10 V, low-ESR radial | Panasonic EEU-FR1A102 |
| C2, C4 | 2 | 100 nF, 25 V, X7R, 0805 | Murata GRM21BR71E104KA01L |
| C5 | 1 | 470 nF, 10 V or higher, X7R, 0805 | Murata GRM21BR71A474KA73L |
| R1-R5, R13-R15, R24-R27 | 12 | 10 k, 0805 | Yageo RC0805FR-0710KL |
| R10-R12 | 3 | 220 ohm, 0805 | Yageo RC0805FR-07220RL |
| R20-R23 | 4 | 1 k, 0805 | Yageo RC0805FR-071KL |
| F1 holder | 1 | Mini blade PCB holder | Keystone 3568 |
| F1 fuse | 1 | 10 A mini blade fuse | Littelfuse 0297010.WXNV |

Off-board: only a four-wire Micro-Fit cable from J12 to the Raspberry Pi GPIO power and ground pins. The 5 V buck converter is now on the PCB.
