# Power and wiring plan

## Power tree

```text
3S LiPo XT60
  -> F1 15 A main fuse -> LTC4365 + back-to-back Q5/Q6 -> VBAT_SW
       -> U1 5 V logic -> ESP32 / control
       -> U4 5.1 V -> F3 5 A -> J9 -> Raspberry Pi 5
       -> J18 external latching E-stop loop -> ACT_VBAT
            -> F5 -> left VNH5019 -> left motor
            -> F6 -> right VNH5019 -> right motor
            -> U10 6 V -> F2 -> MG996R
                            -> U16 4.85 V -> F9 -> MG90S
            -> U11 8.4 V -> F4 -> Miuzei main servo
```

The E-stop removes wheel and servo energy while leaving the Pi/ESP alive. Use the exact external arrangement shown on sheet 00: J21.1 -> Schneider XB5AS8442 normally-closed button -> Panasonic CB1aF-RM-12V-A-5 relay coil -> J21.2. Connect the relay's normally-open 40 A contact across J18. Pressing the button de-energizes the relay, so an open wire also stops the actuators.

`SERVO_POWER_ENABLE` from Raspberry Pi GPIO17 must be driven high before U10/U11 start. It defaults low. Wheel drivers remain electrically powered after J18 closes, but their PWM/INA/INB inputs have firm hardware pull-downs.

D21 is a local bidirectional TVS on `ACT_VBAT`, so motor regeneration remains clamped even when J18 opens. Do not place motor current through the push-button contact; it switches only the selected relay's approximately 134 mA coil. The relay contains suppression and its DC-rated NO contact carries the actuator current.

## Battery limits

The current battery is 3S: 12.6 V full, 11.1 V nominal. A larger-capacity 3S pack is compatible if polarity is correct, its connector/wiring can safely supply the robot, and it is charged with a proper balance charger. A higher C rating does not force current into the robot; it increases how much fault current the pack can supply, making fusing more important.

U12 and Q5/Q6 now disconnect the entire board at approximately 9.62 V and reconnect at approximately 10.10 V; the OV threshold is approximately 13.79 V. This prevents continued whole-pack discharge after a software crash. It is not a cell-balancing BMS and cannot detect one weak cell hidden by the other two, so continue charging through a proper 3S balance charger and periodically verify individual cell voltages.

## External wire starting points

| Path | Suggested wire |
|---|---|
| XT60, F1, J18, main distribution | 14 AWG silicone |
| Motor red/white to J15/J16 | 18 AWG, twisted pair |
| Pi power, two 5 V + two GND contacts | 18–20 AWG |
| Servo power/ground | 20–22 AWG, sized for the actual lead/connector |
| Encoder, PWM, UART, I2C | 24–26 AWG |

Twist each motor power pair. Keep it physically away from encoder, UART, camera, and antenna wiring. Fit the specified 100 nF capacitor directly across each motor's power terminals.

## PCB current routing starting points

Use a four-layer, preferably 2 oz outer-copper board. Width depends on copper thickness, layer, airflow, length, and allowed temperature rise, so final values must be calculated in the PCB tool/board-house calculator.

- Use pours for `VBAT_SW`, `ACT_VBAT`, motor outputs, Pi 5 V, and servo rails.
- Keep every motor and buck high-current loop short.
- Give each VNH5019 exposed pad its own same-net copper and thermal vias; pads 31/32/33 are not interchangeable.
- Place the ground return star near the battery distribution, with logic returns separated from actuator pulses until that point.
- Use at least two vias in parallel whenever a multi-amp rail changes layers; more are normally appropriate.
- Keep switch-node copper as small as possible and never route feedback/ADC/encoder traces through it.

## First-power procedure

1. Inspect polarity, solder bridges, exposed-pad alignment, and connector pin 1.
2. Leave Pi, ESP32 carrier, motors, encoders, and servos disconnected.
3. Power from a current-limited bench supply at 10.5–12 V through a small temporary fuse.
4. Slowly sweep the input down and confirm whole-board cutoff near 9.62 V and recovery near 10.10 V.
5. Verify 5 V logic, then 5.1 V Pi, 6 V servo, and 8.4 V servo rails at their test points with dummy loads.
6. Check regulator startup, ripple, switch node, and temperature before connecting electronics.
7. Test one motor driver with its wheel unloaded, then stalled only long enough for a controlled current measurement.
8. Connect the Pi and servos last. Never connect Pi USB-C power and J9 power simultaneously.

On Pi 5, configure `dtoverlay=uart0-pi5`, disable the serial console, and validate the direct 5.1 V supply before enabling the higher USB-current setting. J9 bypasses USB-C PD negotiation.
