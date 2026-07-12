# Controller R1 design review and next steps

## What is now on the schematic

- 3S LiPo XT60 input, external 15 A blade fuse position, latching E-stop position, TVS clamp, bulk capacitor, and battery-voltage divider.
- Two protected VNH5019A-E wheel H-bridges with one six-pin JST-PH motor/encoder connector each plus separate large red/white motor-power solder pads, local bulk capacitors, control pull-downs, fault network, and current-sense filtering.
- ESP32-PICO-KIT V4.1 removable-carrier footprint using the confirmed 17.78 mm socket-row spacing.
- Raspberry Pi 3.3 V UART/control header plus a dedicated **TPS54560B 5 V / 5 A** Pi/Hailo buck circuit and a 2x2 Mini-Fit Jr output connector.
- Separate LM2596S 5 V control rail for the ESP32/logic only.
- Encoder headers with pull-ups, RC filters, and Schmitt buffers.
- PCA9685 servo controller, an on-board 8.4 V / 5 A TPS54560B rail for the Miuzei main servo, a separate 6 V / 5 A TPS54560B rail for the MG996R/MG90S, three servo headers, protection/bulk capacitance, and rail-status LEDs.

## Design checks completed

- KiCad electrical-rules check: **0 errors, 0 warnings**.
- BOM exported from the schematic.
- The actual KiCad project is split into a hierarchy overview plus six readable circuit sheets. `pickleball_robot_controller.pdf` is a seven-page export made directly by KiCad—there is no HTML or presentation-style substitute.
- Exact net names and every part/value remain available in the KiCad file and BOM.

## Still required before ordering a PCB

1. **Measure GA25-370 stall current** at a controlled 12 V supply if you later want to reduce copper/fuse margins. The current prototype assumption is 3 A peak per wheel, not a measurement.
2. Confirm the exact motor connector, Mini-Fit Jr connector, servo connector, and fuse-holder mechanical footprints against the listings/datasheets you will buy.
3. Follow the TPS54560B reference-layout rules exactly: tight input capacitor loop, very small switch-node copper, thermal pad with thermal vias, feedback away from the switch node.
4. Follow ST's VNH5019 exposed-pad/thermal-via recommendation. This part is a reflow/hot-air part, not a normal soldering-iron part.
5. Verify the servo rail at 6 V with a dummy load before connecting a servo. Its on-board converter is rated at 5 A; do not deliberately hold all servos stalled together.
6. Make the PCB four layers with a solid ground plane and 2 oz outer copper if the fabricator offers it.
7. Add physical safety hardware: external blade fuse near the battery, latching E-stop/disconnect, battery restraint, and insulated covers for all high-current terminals.

## Why motor stall current matters

Stall current is the highest current a DC motor draws: it occurs when a wheel starts abruptly, gets jammed, or is held still while powered. It determines the required motor-driver rating, fuse size, connector rating, wire gauge, PCB copper width, capacitor stress, and heat. The normal rolling current is not enough to size those parts safely.

## First PCB-layout rules

- `VBAT_SW`, motor outputs, servo 6 V, and high-current returns: copper pours where possible; 5–8 mm wide as a starting point on 2 oz outer layers.
- Individual wheel paths and the Pi 5 V path: 3–4 mm minimum starting width on 2 oz outer layers.
- Logic traces: 0.25–0.30 mm is fine.
- Keep the TPS54560B and LM2596 switch nodes tiny and far from encoders/UART/ESP32 antenna.
- Join noisy motor/servo returns to the main battery return at a controlled star/distribution area rather than routing them through the ESP32/Pi return.

## Before first power-up

1. Inspect for shorts, then power from a current-limited bench supply—not the LiPo.
2. Test U1 first: confirm clean 5 V control rail before inserting the ESP32.
3. Test U4 with a dummy 5 V load, then confirm the Pi connector polarity and voltage before connecting the Pi.
4. Test the servo supply separately at 6 V before connecting servos.
5. Test one wheel motor at a time with the wheel off the floor and a small temporary fuse.
