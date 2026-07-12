# Final pre-PCB design review

## What now passes

- KiCad ERC: zero errors and zero warnings.
- `audit_design.py`: passes diode polarity, XT60 polarity, regulator-divider, UVLO, DNP and off-board-part checks that ERC cannot understand.
- Seven readable hierarchical sheets plus a root overview; PDF exports directly from KiCad.
- Correct photographed ESP32 carrier row spacing and corrected antenna/USB orientation.
- Correct right-motor GPIO13 physical pad; Pi UART moved off USB-UART GPIO1/3; servo OE moved off boot GPIO2.
- Left/right driver diagnostics are Schottky-aggregated to ESP GPIO23, J10 and the fault LED without using a strap pin.
- Motor current ADCs and battery ADC have series/filter/clamp protection.
- Four encoder inputs have cable resistors, Schmitt buffers, individual bypass capacitors, and filtered encoder power.
- Motor connector order and separate large motor-wire pads match the user's photographed harness description.
- Three independently commanded servo outputs; main servo at 8.4 V, other two at 6 V.
- Corrected TPS54560 feedback and compensation networks, reference-style ceramic output banks, reduced startup bulk, and exact through-hole fuse-holder footprints.
- Real external E-stop series connector, local actuator-regeneration TVS, actuator/logic power separation, Pi-controlled default-off servo enable, status LEDs, and 51 compact bare-copper test pads excluded from assembly BOM.
- Every catch diode, ADC clamp and LED has been polarity-checked; TVSs are explicitly bidirectional `CA` parts.
- Pi-buck EN uses a 267 kΩ/34.0 kΩ UVLO divider and is no longer exposed directly to 12.6 V.
- Custom VNH5019 footprint parses in KiCad and provides windowed paste plus three separate thermal-via areas.

## Remaining gates — do not send Gerbers until these are closed

1. **Battery protection:** add/choose a genuine hardware 3S undervoltage cutoff. Firmware voltage sensing is not sufficient protection against a crashed controller.
2. **Regulator validation:** confirm the selected Murata/Samsung MLCC DC-bias curves, then verify U4/U10/U11 stability, startup, load steps, ripple, and temperature on the first prototype. Leave optional bulk and snubbers DNP initially.
3. **Mechanical confirmation:** print the PCB 1:1 and place the real ESP32, J4/J5 harness, Mini-Fit Jr, terminal blocks, fuse holders, capacitors, and servo plugs on it.
4. **Motor current:** a 5 A branch allowance is conservative, not a claim that the motor normally draws 5 A. Measure the actual stall/current-limited behavior before reducing fuse, connector, wire, or copper margin.
5. **Servo identity:** confirm the exact Miuzei SKU allows continuous 8.4 V and verify MG996R/MG90S lead polarity.
6. **Logic level:** bench-confirm all three servo models recognize 3.3 V PWM; add a 5 V AHCT buffer if any model does not.
7. **E-stop hardware:** select an exact NC latching E-stop/contact path with a suitable 12 V DC motor-load interruption and inrush rating.

## PCB-layout checklist

- Start with four layers and a solid uninterrupted ground plane.
- Put the three buck converters and two H-bridges at board edges with short high-current connections and thermal copper.
- Put ESP32 antenna at an edge with copper/component keepout; put USB at an accessible edge.
- Keep encoder/UART/I2C/ADC sections away from motors, inductors, diodes, and switch nodes.
- Add board net classes for logic, auxiliary power, Pi/servo power, battery, and motor outputs.
- Use star distribution for actuator branches and Kelvin feedback/sense routing.
- Add four mounting holes, motor-wire strain-relief holes, polarity/pin-1 legends, fuse values, rail names, and test-point names.
- Verify every custom footprint against the manufacturer drawing and inspect paste layers for U2/U3/U4/U10/U11.
- Run PCB DRC, inspect unrouted count, compare schematic/PCB nets, and inspect Gerber copper/mask/paste/silkscreen/drill files.

## Recommended prototype strategy

Populate and validate in stages: input/5 V logic; Pi buck; one motor driver; encoder front end; second motor driver; 6 V servo rail/PCA9685; 8.4 V rail. Use a bench supply and dummy loads before the LiPo. This makes the first board debuggable instead of turning every subsystem on at once.
