# Final pre-PCB design review

## What now passes

- KiCad ERC: zero errors and zero warnings.
- `audit_design.py`: passes diode polarity, XT60 polarity, regulator dividers, whole-board LVD thresholds/topology, servo-buffer count, DNP and off-board-part checks that ERC cannot understand.
- Eight readable hierarchical sheets plus a root overview; battery safety has its own page.
- Correct photographed ESP32 carrier row spacing and corrected antenna/USB orientation.
- Correct right-motor GPIO13 physical pad; Pi UART moved off USB-UART GPIO1/3; servo OE moved off boot GPIO2.
- Left/right driver diagnostics are Schottky-aggregated to ESP GPIO23, J10 and the fault LED without using a strap pin.
- Motor current ADCs and battery ADC have series/filter/clamp protection.
- Four encoder inputs have cable resistors, Schmitt buffers, individual bypass capacitors, and filtered encoder power.
- Motor connector order and separate large motor-wire pads match the user's photographed harness description.
- Three independently commanded servo outputs: Miuzei at 8.4 V, MG996R at 6 V, and official MG90S at 4.85 V.
- Three AHCT buffers translate every servo command to guaranteed 4.85 V PWM, go high-impedance with PCA9685 OE, and lose power when the servo rails are disabled.
- LTC4365 plus back-to-back TO-220 MOSFETs disconnects the whole board at about 9.62 V and reconnects at about 10.10 V.
- Exact fail-safe E-stop wiring is selected: XB5AS8442 NC button controlling a resistor-suppressed Panasonic 40 A automotive relay.
- Corrected TPS54560 feedback and compensation networks, reference-style ceramic output banks, reduced startup bulk, and exact through-hole fuse-holder footprints.
- Real external E-stop series connector, local actuator-regeneration TVS, actuator/logic power separation, Pi-controlled default-off servo enable, status LEDs, and 51 compact bare-copper test pads excluded from assembly BOM.
- Every catch diode, ADC clamp and LED has been polarity-checked; TVSs are explicitly bidirectional `CA` parts.
- Pi-buck EN uses a 267 kΩ/34.0 kΩ UVLO divider and is no longer exposed directly to 12.6 V.
- Custom VNH5019 footprint parses in KiCad and provides windowed paste plus three separate thermal-via areas.

## Remaining gates — do not send Gerbers until these are closed

1. **Battery qualification:** bench-sweep U12 cutoff/reconnect and remember it is whole-pack protection, not cell balancing or charging protection.
2. **Regulator validation:** confirm the selected Murata/Samsung MLCC DC-bias curves, then verify U4/U10/U11 stability, startup, load steps, ripple, and temperature on the first prototype. Leave optional bulk and snubbers DNP initially.
3. **Mechanical confirmation:** print the PCB 1:1 and place the real ESP32, J4/J5 harness, Mini-Fit Jr, terminal blocks, fuse holders, capacitors, TO-220 MOSFETs, and servo plugs on it.
4. **Motor current:** a 5 A branch allowance is conservative, not a claim that the motor normally draws 5 A. Measure the actual stall/current-limited behavior before reducing fuse, connector, wire, or copper margin.
5. **Servo identity:** confirm the exact purchased Miuzei SKU allows continuous 8.4 V and verify all servo lead polarities. PWM voltage uncertainty is removed by U13–U15.
6. **E-stop harness:** continuity-test the NC-button/relay-coil fail-safe behavior and verify J18 opens when the button is pressed or any coil-loop wire is removed.

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
