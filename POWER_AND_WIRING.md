# Power and wiring plan

## Power tree

```text
3S LiPo XT60
  -> F1 15 A main fuse -> VBAT_SW
       -> U1 5 V logic -> ESP32 / control
       -> U4 5.1 V -> F3 5 A -> J9 -> Raspberry Pi 5
       -> J18 external latching E-stop loop -> ACT_VBAT
            -> F5 -> left VNH5019 -> left motor
            -> F6 -> right VNH5019 -> right motor
            -> U10 6 V -> F2 -> MG996R + MG90S
            -> U11 8.4 V -> F4 -> Miuzei main servo
```

The E-stop removes wheel and servo energy while leaving the Pi/ESP alive to log the event and shut down cleanly. J18 is a real series connection: actuators remain off if the external switch is not connected/closed.

`ACTUATOR_ENABLE` from Raspberry Pi GPIO17 must be driven high before U10/U11 start. It defaults low. Wheel drivers remain electrically powered after J18 closes, but their PWM/INA/INB inputs have firm hardware pull-downs.

## Battery limits

The current battery is 3S: 12.6 V full, 11.1 V nominal. A larger-capacity 3S pack is compatible if polarity is correct, its connector/wiring can safely supply the robot, and it is charged with a proper balance charger. A higher C rating does not force current into the robot; it increases how much fault current the pack can supply, making fusing more important.

The board measures battery voltage but does not yet provide a true hardware 3S undervoltage cutoff. Do not rely on the TPS54560 internal UVLO; it is far below a safe 3S discharge voltage. Add a suitable battery protector/supervisor or stop the robot conservatively in software while developing.

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
3. Power from a current-limited bench supply at 9–12 V through a small temporary fuse.
4. Verify 5 V logic, then 5.1 V Pi, 6 V servo, and 8.4 V servo rails at their test points with dummy loads.
5. Check regulator startup, ripple, switch node, and temperature before connecting electronics.
6. Test one motor driver with its wheel unloaded, then stalled only long enough for a controlled current measurement.
7. Connect the Pi and servos last. Never connect Pi USB-C power and J9 power simultaneously.
