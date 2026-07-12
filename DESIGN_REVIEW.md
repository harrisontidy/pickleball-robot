# Final pre-PCB design review

## What now passes

- KiCad ERC: zero errors and zero warnings.
- Seven readable hierarchical sheets plus a root overview; PDF exports directly from KiCad.
- Correct photographed ESP32 carrier row spacing and corrected antenna/USB orientation.
- Correct right-motor GPIO13 physical pad; Pi UART moved off USB-UART GPIO1/3; servo OE moved off boot GPIO2.
- Separate left/right motor diagnostics reach ESP GPIO23/GPIO5 and are diode-aggregated for J10/LED.
- Motor current ADCs and battery ADC have series/filter/clamp protection.
- Four encoder inputs have cable resistors, Schmitt buffers, individual bypass capacitors, and filtered encoder power.
- Motor connector order and separate large motor-wire pads match the user's photographed harness description.
- Three independently commanded servo outputs; main servo at 8.4 V, other two at 6 V.
- Corrected TPS54560 feedback and compensation networks, reference-style ceramic output banks, reduced startup bulk, and exact through-hole fuse-holder footprints.
- Real external E-stop series connector, actuator/logic power separation, Pi-controlled default-off servo enable, status LEDs, and 51 labelled test points.
- Custom VNH5019 footprint parses in KiCad and provides windowed paste plus three separate thermal-via areas.

## Remaining gates — do not send Gerbers until these are closed

1. **Battery protection:** add/choose a genuine hardware 3S undervoltage cutoff. Firmware voltage sensing is not sufficient protection against a crashed controller.
2. **Regulator validation:** choose final output MLCC MPNs using their DC-bias curves, then verify U4/U10/U11 stability, startup, load steps, ripple, and temperature on the first prototype. Equations reduce risk but do not replace bench validation.
3. **Mechanical confirmation:** print the PCB 1:1 and place the real ESP32, J4/J5 harness, Mini-Fit Jr, terminal blocks, fuse holders, capacitors, and servo plugs on it.
4. **Motor current:** a 5 A branch allowance is conservative, not a claim that the motor normally draws 5 A. Measure the actual stall/current-limited behavior before reducing fuse, connector, wire, or copper margin.
5. **Servo identity:** confirm the exact Miuzei SKU allows continuous 8.4 V and verify MG996R/MG90S lead polarity.

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
