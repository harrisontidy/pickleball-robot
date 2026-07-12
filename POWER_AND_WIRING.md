# Power and wiring plan

Use one 3S LiPo battery. Do not add a second battery for the Raspberry Pi.

```text
3S LiPo (XT60)
  |
  +-- 15 A fuse + emergency stop --> wheel-motor rail --> VNH5019 drivers
  |
  +-- 5 V / 5 A buck regulator --> Raspberry Pi 5 + Hailo
  |
  +-- 5 V / 1 A buck regulator --> ESP32 + encoder logic + PCA9685 logic
  |
  +-- 6 V / 10 A regulator --> three arm servos
```

The Pi must use its own 5 V / 5 A regulator because the board's small LM2596S logic converter is only for the ESP32, encoders, LEDs, and PCA9685. A Pi 5 plus Hailo can need substantially more current than that small rail can safely supply.

For a first build, use an external high-quality 5 V / 5 A buck regulator between the 3S LiPo and the board's `PI_5V_5A_INPUT` connector. The Pololu D36V50F5 is one appropriate 5.5 A option. A later PCB revision can integrate an LM2678S-5.0 5 A buck circuit, but it needs careful layout and thermal design.

The arm servo rail also needs its own **regulated** 6 V, high-current supply. Do not attach the 3S LiPo directly to the servo connectors.

## Initial wire sizes

| Connection | Initial wire | Notes |
|---|---|---|
| Battery XT60 to fuse/E-stop/distribution | 14 AWG silicone | keep short |
| Distribution to each wheel driver | 16 AWG silicone | twist each motor-pair cable |
| Driver to each GA25-370 motor | 18 AWG silicone | short run preferred |
| 6 V servo regulator to servo distribution | 14–16 AWG silicone | high current, short run |
| Individual standard servo power lead | 20–22 AWG | use the supplied leads only for short runs |
| Pi 5 V regulator to Pi | 18–20 AWG | short, low-resistance cable |
| ESP32/logic rail | 24–26 AWG | low current |
| Encoder/UART/I2C signal wires | 26–28 AWG | keep away from motor wires |

These are conservative starting values. Measure the actual wheel-motor stall current before finalizing the fuse, connectors, and PCB copper widths.

## PCB copper starting point

- Prefer a four-layer board with a solid ground plane and 2 oz outer copper.
- Battery/motor/servo pours: at least 5–8 mm wide wherever space allows; use copper pours instead of narrow traces.
- Per-wheel motor paths: at least 3–4 mm wide on 2 oz outer copper, with extra copper around each VNH5019.
- Pi 5 V path: at least 3–4 mm wide on 2 oz outer copper.
- ESP32 and signal traces: 0.25–0.3 mm is fine.
- Use multiple vias in parallel when high-current paths must change layers.
- Keep motor and servo returns away from the ESP32/Pi logic ground paths; join them at the battery/distribution star point.

Do not finalize this layout until the wheel-motor stall current has been measured.
