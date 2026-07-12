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
  +-- 6 V / 5 A regulator --> three arm servos
```

The Pi must use its own 5 V / 5 A regulator because the board's small LM2596S logic converter is only for the ESP32, encoders, LEDs, and PCA9685. A Pi 5 plus Hailo can need substantially more current than that small rail can safely supply.

This revision includes that regulator on the PCB: **U4, TPS54560BDDA**, a 4.5–60 V, 5 A buck controller with its external diode, inductor, feedback, compensation, input capacitors, output capacitors, output fuse, and Mini-Fit Jr Pi connector. The 12 V nominal → 5 V / 5 A component values follow TI's documented reference circuit. The Pi rail is `PI_5V`; it is protected by F3 and must only feed the Pi/Hailo branch.

The PCB now includes a second TPS54560B buck circuit for the servo branch: **6 V / 5 A**, followed by a 7.5 A fuse, transient clamp, bulk capacitor, and three servo headers. This is a sensible hobby-prototype rating for the 25 kg main servo, MG996R elbow servo, and MG90S wrist servo when they are not deliberately stalled together. Do not put 3S battery voltage directly into any servo.

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

Do not finalize this layout until the wheel-motor stall current has been measured and the two buck regulators have been checked against their manufacturer layout guidance.
