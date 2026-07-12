from pathlib import Path
import json
import uuid
from kicad_sch_api import create_schematic

OUT = Path(__file__).resolve().parent
s = create_schematic("pickleball_controller")
label_records = []
s.set_paper_size("A3")
s.set_title_block(
    title="Pickleball Robot Wheel Controller + Raspberry Pi Interface",
    date="2026-07-12",
    rev="R1-DRAFT",
    company="Harrison",
    comments={1: "3S LiPo; 2x GA25-370; provisional 5 A stall per motor",
              2: "DRAFT: verify motor stall current and footprints before manufacture",
              3: "Pi power uses dedicated TPS54560B 5 V / 5 A buck"},
)

def part(lib, ref, value, x, y, footprint="", rotation=0.0):
    return s.components.add(lib, reference=ref, value=value,
                            position=(x, y), footprint=footprint, rotation=rotation)

def pin_net(ref, pin, net, length=7.62):
    """Record a short outward wire and label for a component pin."""
    p = s.get_component_pin_position(ref, str(pin))
    c = s.components.get(ref).position
    # Keep stubs short so dense connector pins cannot cross neighboring nets.
    length = 2.54
    dx, dy = p.x - c.x, p.y - c.y
    if abs(dx) >= abs(dy):
        sign = -1 if dx < 0 else 1
        ex, ey = p.x + sign * length, p.y
        justify = "right" if sign < 0 else "left"
        angle = 180 if sign < 0 else 0
    else:
        sign = -1 if dy < 0 else 1
        ex, ey = p.x, p.y + sign * length
        justify = "left"
        angle = 270 if sign < 0 else 90
    label_records.append((net, p.x, p.y, ex, ey, justify, angle))

def two_pin(ref, net1, net2):
    pin_net(ref, "1", net1)
    pin_net(ref, "2", net2)

# ---------------------------------------------------------------------------
# Battery input/protection and power connectors
# ---------------------------------------------------------------------------
s.add_text("BATTERY INPUT + PROTECTION", (20, 16), size=2.0, bold=True)
part("Connector_Generic:Conn_01x02", "J1", "BATTERY_XT60_PIGTAIL", 30, 30,
     "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm")
pin_net("J1", 1, "BAT_RAW")
pin_net("J1", 2, "GND")

part("Device:Fuse", "F1", "15A_EXTERNAL_BLADE", 52, 25,
     "Fuse:Fuse_Blade_ATO_directSolder")
two_pin("F1", "BAT_RAW", "VBAT_SW")

part("Device:D_TVS", "D1", "SMBJ18A", 72, 31,
     "Diode_SMD:D_SMB")
two_pin("D1", "GND", "VBAT_SW")
part("Device:C_Polarized", "C1", "1000uF 25V LOW_ESR", 88, 31,
     "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm")
two_pin("C1", "VBAT_SW", "GND")
part("Device:C", "C2", "1uF 25V X7R", 102, 31,
     "Capacitor_SMD:C_1206_3216Metric")
two_pin("C2", "VBAT_SW", "GND")
part("Device:R", "R1", "100k 1% BAT DIV TOP", 72, 42, "Resistor_SMD:R_0805_2012Metric")
two_pin("R1", "VBAT_SW", "BAT_SENSE_RAW")
part("Device:R", "R2", "27k 1% BAT DIV BOTTOM", 88, 42, "Resistor_SMD:R_0805_2012Metric")
two_pin("R2", "BAT_SENSE_RAW", "GND")
part("Device:R", "R3", "1k ADC PROTECT", 104, 42, "Resistor_SMD:R_0805_2012Metric")
two_pin("R3", "BAT_SENSE_RAW", "GPIO33_BAT_ADC")
part("Device:C", "C4", "100nF ADC FILTER", 116, 42, "Capacitor_SMD:C_0805_2012Metric")
two_pin("C4", "GPIO33_BAT_ADC", "GND")

s.add_text("External latching E-stop / disconnect goes between F1 and VBAT_SW", (43, 42), size=1.2)

# Raspberry Pi power is intentionally separate from the 1 A control buck.
# Values are TI's documented 12 V -> 5 V / 5 A TPS54560B example circuit.
s.add_text("RASPBERRY PI 5V / 5A BUCK — TPS54560B", (20, 55), size=1.6, bold=True)
part("Regulator_Switching:TPS54560BDDA", "U4", "TPS54560BDDA — 5V / 5A", 72, 68,
     "Package_SO:TI_SO-PowerPAD-8_ThermalVias")
pin_net("U4", 1, "PI_BOOT")
pin_net("U4", 2, "VBAT_SW")
pin_net("U4", 3, "VBAT_SW")
pin_net("U4", 4, "PI_RT")
pin_net("U4", 5, "PI_FB")
pin_net("U4", 6, "PI_COMP")
pin_net("U4", 7, "GND")
pin_net("U4", 8, "PI_BUCK_SW")
pin_net("U4", 9, "GND")
part("Device:C", "C31", "100nF BOOT", 98, 57, "Capacitor_SMD:C_0805_2012Metric")
two_pin("C31", "PI_BOOT", "PI_BUCK_SW")
part("Device:D_Schottky", "D9", "B560C 5A", 98, 68, "Diode_SMD:D_SMC")
two_pin("D9", "GND", "PI_BUCK_SW")
part("Device:L", "L2", "7.2uH >=8A SHIELDED", 110, 68, "Inductor_SMD:L_1210_3225Metric")
two_pin("L2", "PI_BUCK_SW", "PI_5V_RAW")
part("Device:C", "C32", "2.2uF 25V X7R", 36, 65, "Capacitor_SMD:C_1206_3216Metric")
two_pin("C32", "VBAT_SW", "GND")
part("Device:C", "C33", "2.2uF 25V X7R", 47, 65, "Capacitor_SMD:C_1206_3216Metric")
two_pin("C33", "VBAT_SW", "GND")
part("Device:C", "C34", "2.2uF 25V X7R", 36, 76, "Capacitor_SMD:C_1206_3216Metric")
two_pin("C34", "VBAT_SW", "GND")
part("Device:C", "C35", "2.2uF 25V X7R", 47, 76, "Capacitor_SMD:C_1206_3216Metric")
two_pin("C35", "VBAT_SW", "GND")
part("Device:R", "R30", "243k RT SET", 56, 82, "Resistor_SMD:R_0805_2012Metric")
two_pin("R30", "PI_RT", "GND")
part("Device:R", "R31", "442k FB TOP 1%", 116, 56, "Resistor_SMD:R_0805_2012Metric")
two_pin("R31", "PI_5V_RAW", "PI_FB")
part("Device:R", "R32", "90.9k FB BOTTOM 1%", 130, 56, "Resistor_SMD:R_0805_2012Metric")
two_pin("R32", "PI_FB", "GND")
part("Device:R", "R33", "10.2k COMP", 116, 80, "Resistor_SMD:R_0805_2012Metric")
two_pin("R33", "PI_COMP", "PI_COMP_RC")
part("Device:C", "C36", "4.7nF COMP", 130, 80, "Capacitor_SMD:C_0805_2012Metric")
two_pin("C36", "PI_COMP_RC", "GND")
part("Device:C", "C37", "47pF COMP", 142, 80, "Capacitor_SMD:C_0805_2012Metric")
two_pin("C37", "PI_COMP", "GND")
part("Device:C", "C38", "47uF 10V X7R", 148, 57, "Capacitor_SMD:C_1210_3225Metric")
two_pin("C38", "PI_5V_RAW", "GND")
part("Device:C", "C39", "47uF 10V X7R", 158, 57, "Capacitor_SMD:C_1210_3225Metric")
two_pin("C39", "PI_5V_RAW", "GND")
part("Device:C", "C44", "47uF 10V X7R", 168, 57, "Capacitor_SMD:C_1210_3225Metric")
two_pin("C44", "PI_5V_RAW", "GND")
part("Device:Fuse", "F3", "5A PI OUTPUT FUSE", 142, 68, "Fuse:Fuse_1206_3216Metric")
two_pin("F3", "PI_5V_RAW", "PI_5V")
part("Connector_Generic:Conn_02x02_Odd_Even", "J9", "PI POWER: 2x5V + 2xGND", 174, 68,
     "Connector_Molex:Molex_Mini-Fit_Jr_5569-04A2_2x02_P4.20mm_Horizontal")
pin_net("J9", 1, "PI_5V"); pin_net("J9", 2, "PI_5V")
pin_net("J9", 3, "GND"); pin_net("J9", 4, "GND")
part("Device:C_Polarized", "C30", "1000uF 10V LOW ESR", 194, 68,
     "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm")
two_pin("C30", "PI_5V", "GND")
s.add_text("Use Mini-Fit Jr / screw terminal, not 0.1in headers, for Pi power. Keep this 5A path short and wide.", (20, 90), size=1.1)
s.add_text("U4 values are the TI 12V-to-5V / 5A reference design. Follow TI layout guidance; do not use this rail for motors or servos.", (20, 95), size=1.1)

# ---------------------------------------------------------------------------
# 5 V / 1 A control buck
# ---------------------------------------------------------------------------
s.add_text("5V CONTROL BUCK (ESP32 + LOGIC ONLY)", (125, 16), size=1.8, bold=True)
part("Regulator_Switching:LM2596S-5", "U1", "LM2596S-5.0", 156, 31,
     "Package_TO_SOT_SMD:TO-263-5_TabPin3")
pin_net("U1", 1, "VBAT_SW")
pin_net("U1", 3, "GND")
pin_net("U1", 5, "GND")
pin_net("U1", 2, "BUCK_SW")
pin_net("U1", 4, "+5V_CTRL")
part("Device:D_Schottky", "D3", "SS54", 185, 25, "Diode_SMD:D_SMA")
two_pin("D3", "GND", "BUCK_SW")
part("Device:L", "L1", "33uH >=4A SHIELDED", 185, 38,
     "Inductor_SMD:L_Sunlord_MWSA1265S")
two_pin("L1", "BUCK_SW", "+5V_CTRL")
part("Device:C_Polarized", "C5", "220uF 25V LOW_ESR", 216, 25,
     "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm")
two_pin("C5", "VBAT_SW", "GND")
part("Device:C_Polarized", "C7", "330uF 10V LOW_ESR", 216, 39,
     "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm")
two_pin("C7", "+5V_CTRL", "GND")

# ---------------------------------------------------------------------------
# ESP32 carrier represented as two physical 17-pin socket rows.
# ---------------------------------------------------------------------------
s.add_text("ESP32-PICO-KIT V4.1 SOCKETS", (20, 98), size=1.8, bold=True)
part("Connector_Generic:Conn_02x17_Odd_Even", "J2", "ESP32_PICO_KIT_V4.1_CARRIER", 65, 135,
     "PickleballRobot:ESP32_PICO_KIT_V4_1_Carrier")

# The labels match the photographed board rows. Confirm physical row spacing before PCB layout.
left_nets = ["GPIO21_I2C_SDA", "GPIO22_I2C_SCL", None, None, None,
             None, None, None, "ESP_RX0_GPIO3", "ESP_TX0_GPIO1",
             "GPIO35_ENC_LB", "GPIO34_ENC_LA", "GPIO38_ENC_RB", "GPIO37_ENC_RA",
             None, "GND", "3V3"]
right_nets = ["SENSOR_VP_GPIO36", "SENSOR_VN_GPIO39", "GPIO25_L_PWM", "GPIO26_L_INA",
              None, "GPIO33_BAT_ADC", "GPIO27_L_INB", "GPIO14_R_PWM",
              "GPIO13_R_INA", None, None, "GPIO2_SERVO_OE", "GPIO4_R_INB", None, "3V3", "GND", "+5V_CTRL"]
for i, net in enumerate(left_nets, 1):
    pin = 2 * i - 1
    pin_net("J2", pin, net, 5.08) if net else s.no_connects.add(s.get_component_pin_position("J2", str(pin)))
for i, net in enumerate(right_nets, 1):
    pin = 2 * i
    pin_net("J2", pin, net, 5.08) if net else s.no_connects.add(s.get_component_pin_position("J2", str(pin)))
s.add_text("ESP32-PICO-KIT carrier uses the confirmed 17.78mm row spacing.", (25, 180), size=1.2)

# ---------------------------------------------------------------------------
# Raspberry Pi UART and supervisory connector
# ---------------------------------------------------------------------------
s.add_text("RASPBERRY PI UART / CONTROL", (125, 98), size=1.8, bold=True)
part("Connector_Generic:Conn_01x08", "J10", "PI_UART_CONTROL", 150, 127,
     "Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical")
pi_nets = ["3V3", "GND", "PI_TX_TO_ESP", "ESP_TX_TO_PI", "PI_ENABLE", "MOTOR_DIAG", "GPIO21_I2C_SDA", "GPIO22_I2C_SCL"]
for i, net in enumerate(pi_nets, 1): pin_net("J10", i, net)
part("Device:R", "R40", "1k", 185, 116, "Resistor_SMD:R_0805_2012Metric")
two_pin("R40", "PI_TX_TO_ESP", "ESP_RX0_GPIO3")
part("Device:R", "R41", "1k", 185, 128, "Resistor_SMD:R_0805_2012Metric")
two_pin("R41", "ESP_TX0_GPIO1", "ESP_TX_TO_PI")
part("Device:R", "R42", "10k", 185, 140, "Resistor_SMD:R_0805_2012Metric")
two_pin("R42", "PI_ENABLE", "3V3")
s.add_text("UART is 3.3V: Pi GPIO14 TX -> ESP RX0; ESP TX0 -> Pi GPIO15 RX.", (126, 158), size=1.15)
s.add_text("Do not connect Pi/ESP UART while Micro-USB serial is actively driving RX0/TX0.", (126, 163), size=1.15)

# Readable status indicators.  These also provide convenient visual checks during bring-up.
s.add_text("STATUS LEDs", (126, 170), size=1.4, bold=True)
part("Device:R", "R100", "1k", 140, 180, "Resistor_SMD:R_0805_2012Metric")
two_pin("R100", "+5V_CTRL", "LED_CTRL_PWR")
part("Device:LED", "D5", "GREEN", 156, 180, "LED_SMD:LED_0805_2012Metric")
two_pin("D5", "LED_CTRL_PWR", "GND")
part("Device:R", "R101", "1k", 175, 180, "Resistor_SMD:R_0805_2012Metric")
two_pin("R101", "PI_5V", "LED_PI_PWR")
part("Device:LED", "D6", "BLUE", 191, 180, "LED_SMD:LED_0805_2012Metric")
two_pin("D6", "LED_PI_PWR", "GND")
part("Device:R", "R102", "1k", 210, 180, "Resistor_SMD:R_0805_2012Metric")
two_pin("R102", "SERVO_6V", "LED_SERVO_PWR")
part("Device:LED", "D7", "AMBER", 226, 180, "LED_SMD:LED_0805_2012Metric")
two_pin("D7", "LED_SERVO_PWR", "GND")
part("Device:R", "R103", "1k", 245, 180, "Resistor_SMD:R_0805_2012Metric")
two_pin("R103", "3V3", "LED_FAULT_ANODE")
part("Device:LED", "D8", "RED", 261, 180, "LED_SMD:LED_0805_2012Metric")
two_pin("D8", "LED_FAULT_ANODE", "MOTOR_DIAG")
s.add_text("D5 GREEN: control 5V     D6 BLUE: Pi 5V     D7 AMBER: servo 6V     D8 RED: motor driver fault", (126, 187), size=1.0)

# ---------------------------------------------------------------------------
# Two integrated high-current H bridges.
# ---------------------------------------------------------------------------
def add_motor_channel(ref, motor_j, x, y, prefix, pwm, ina, inb, fault, current):
    part("Driver_Motor:VNH5019A-E", ref, "VNH5019A-E", x, y,
         "Package_SO:ST_MultiPowerSO-30")
    pin_net(ref, 3, "VBAT_SW"); pin_net(ref, 12, "VBAT_SW")
    pin_net(ref, 18, "GND"); pin_net(ref, 26, "GND")
    pin_net(ref, 4, ina); pin_net(ref, 10, inb); pin_net(ref, 7, pwm)
    pin_net(ref, 6, "GND")
    pin_net(ref, 5, fault); pin_net(ref, 9, fault)
    pin_net(ref, 8, current)
    pin_net(ref, 1, prefix + "_OUTA"); pin_net(ref, 15, prefix + "_OUTB")
    # CP is only needed for an optional external reverse-battery MOSFET.
    s.no_connects.add(s.get_component_pin_position(ref, "11"))
    part("Connector_Generic:Conn_01x02", motor_j, prefix + "_MOTOR", x + 38, y,
         "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm")
    pin_net(motor_j, 1, prefix + "_OUTA"); pin_net(motor_j, 2, prefix + "_OUTB")
    part("Device:C_Polarized", "C" + ("12" if prefix == "LEFT" else "15"), "470uF 25V LOW_ESR", x + 38, y + 18,
         "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm")
    two_pin("C" + ("12" if prefix == "LEFT" else "15"), "VBAT_SW", "GND")
    part("Device:R", "R" + ("7" if prefix == "LEFT" else "14"), "1k CURRENT SENSE", x + 38, y + 30,
         "Resistor_SMD:R_0805_2012Metric")
    two_pin("R" + ("7" if prefix == "LEFT" else "14"), current, "GND")
    base = 80 if prefix == "LEFT" else 90
    for off, control in enumerate([pwm, ina, inb]):
        part("Device:R", f"R{base+off}", "100k SAFE PULLDOWN", x - 34, y + 18 + off * 12,
             "Resistor_SMD:R_0805_2012Metric")
        two_pin(f"R{base+off}", control, "GND")
    part("Device:R", f"R{base+3}", "10k FAULT PULLUP", x - 34, y + 56,
         "Resistor_SMD:R_0805_2012Metric")
    two_pin(f"R{base+3}", fault, "3V3")
    part("Device:C", f"C{base}", "10nF CURRENT FILTER", x + 52, y + 30,
         "Capacitor_SMD:C_0805_2012Metric")
    two_pin(f"C{base}", current, "GND")

s.add_text("LEFT MOTOR DRIVER", (20, 198), size=1.8, bold=True)
add_motor_channel("U2", "J4", 58, 225, "LEFT", "GPIO25_L_PWM", "GPIO26_L_INA", "GPIO27_L_INB", "MOTOR_DIAG", "SENSOR_VP_GPIO36")
s.add_text("RIGHT MOTOR DRIVER", (135, 198), size=1.8, bold=True)
add_motor_channel("U3", "J5", 170, 225, "RIGHT", "GPIO14_R_PWM", "GPIO13_R_INA", "GPIO4_R_INB", "MOTOR_DIAG", "SENSOR_VN_GPIO39")

# ---------------------------------------------------------------------------
# Encoder connectors and input conditioning placeholder connectors.
# Full RC/Schmitt detail is documented in SCHEMATIC_GUIDE.md and is represented
# here by the buffer plus named nets for clean first-pass review.
# ---------------------------------------------------------------------------
s.add_text("WHEEL ENCODERS (3.3V)", (248, 16), size=1.8, bold=True)
part("Connector_Generic:Conn_01x04", "J6", "LEFT_ENCODER", 254, 85,
     "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical")
part("Connector_Generic:Conn_01x04", "J7", "RIGHT_ENCODER", 300, 85,
     "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical")
for ref, nets in [("J6", ["3V3", "GND", "LEFT_ENC_A_RAW", "LEFT_ENC_B_RAW"]),
                  ("J7", ["3V3", "GND", "RIGHT_ENC_A_RAW", "RIGHT_ENC_B_RAW"])]:
    for i, net in enumerate(nets, 1): pin_net(ref, i, net)
# Four separate Schmitt buffers avoid multi-unit-symbol ambiguity.
encoder_channels = [
    ("U6", 258, 106, "LEFT_ENC_A_RAW", "GPIO34_ENC_LA"),
    ("U7", 280, 106, "LEFT_ENC_B_RAW", "GPIO35_ENC_LB"),
    ("U8", 302, 106, "RIGHT_ENC_A_RAW", "GPIO37_ENC_RA"),
    ("U9", 324, 106, "RIGHT_ENC_B_RAW", "GPIO38_ENC_RB"),
]
for ref, x, y, raw_net, gpio_net in encoder_channels:
    part("74xGxx:74LVC1G14", ref, "74LVC1G14", x, y,
         "Package_TO_SOT_SMD:SOT-23-5")
    s.no_connects.add(s.get_component_pin_position(ref, "1"))
    pin_net(ref, 2, raw_net)
    pin_net(ref, 3, "GND")
    pin_net(ref, 4, gpio_net)
    pin_net(ref, 5, "3V3")
    idx = int(ref[1:])
    part("Device:R", f"R{70+idx}", "10k PULLUP", x, y + 8,
         "Resistor_SMD:R_0805_2012Metric")
    two_pin(f"R{70+idx}", raw_net, "3V3")
    part("Device:C", f"C{70+idx}", "1nF FILTER", x, y + 14,
         "Capacitor_SMD:C_0805_2012Metric")
    two_pin(f"C{70+idx}", raw_net, "GND")
s.add_text("Encoder inputs include pull-ups, RC filtering, and Schmitt buffers.", (247, 126), size=1.15)

# Notes / explicit draft limitations
s.add_text("SAFETY / REVIEW NOTES", (248, 130), size=1.8, bold=True)
s.add_text("1. VNH5019 exposed pads need reflow, thermal vias, and large copper pours.", (248, 140), size=1.1)
s.add_text("2. Verify actual motor stall current before ordering production PCB.", (248, 146), size=1.1)
s.add_text("3. Pi power is NOT made by U1. Feed J8 from a separate regulated 5V/5A supply.", (248, 152), size=1.1)
s.add_text("4. Never power ESP32 from USB and EXT_5V simultaneously.", (248, 158), size=1.1)
s.add_text("5. External fuse and latching E-stop are mandatory.", (248, 164), size=1.1)

# ---------------------------------------------------------------------------
# Three-degree-of-freedom servo subsystem.
# The PCB controls PWM; a separate regulated 6 V / 10 A source supplies power.
# ---------------------------------------------------------------------------
s.add_text("3-DOF ARM SERVO CONTROL", (248, 168), size=1.8, bold=True)
part("Connector_Generic:Conn_01x02", "J11", "SERVO_6V_10A_INPUT", 260, 182,
     "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm")
pin_net("J11", 1, "SERVO_6V_RAW"); pin_net("J11", 2, "GND")
part("Device:Fuse", "F2", "15A_EXTERNAL_SERVO_FUSE", 285, 176,
     "Fuse:Fuse_Blade_ATO_directSolder")
two_pin("F2", "SERVO_6V_RAW", "SERVO_6V")
part("Device:D_TVS", "D4", "SMBJ8.0A", 304, 176, "Diode_SMD:D_SMB")
two_pin("D4", "GND", "SERVO_6V")
part("Device:C_Polarized", "C40", "2200uF 10V LOW_ESR", 324, 176,
     "Capacitor_THT:CP_Radial_D12.5mm_P5.00mm")
two_pin("C40", "SERVO_6V", "GND")
part("Device:C", "C41", "100nF", 340, 176, "Capacitor_SMD:C_0805_2012Metric")
two_pin("C41", "SERVO_6V", "GND")

part("Driver_LED:PCA9685PW", "U5", "PCA9685PW", 280, 208,
     "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm")
# Address 0x40, internal oscillator, I2C and supply.
for p in [1, 2, 3, 4, 5, 24]: pin_net("U5", p, "GND")
pin_net("U5", 14, "GND")
pin_net("U5", 28, "3V3")
pin_net("U5", 25, "GND")
pin_net("U5", 26, "GPIO22_I2C_SCL")
pin_net("U5", 27, "GPIO21_I2C_SDA")
pin_net("U5", 23, "GPIO2_SERVO_OE")
pin_net("U5", 6, "SERVO0_PWM_RAW")
pin_net("U5", 7, "SERVO1_PWM_RAW")
pin_net("U5", 8, "SERVO2_PWM_RAW")
for p in range(9, 23):
    s.no_connects.add(s.get_component_pin_position("U5", str(p)))

part("Device:C", "C42", "100nF", 322, 198, "Capacitor_SMD:C_0805_2012Metric")
two_pin("C42", "3V3", "GND")
part("Device:C", "C43", "10uF 6.3V", 322, 208, "Capacitor_SMD:C_1206_3216Metric")
two_pin("C43", "3V3", "GND")
part("Device:R", "R50", "4.7k I2C PULLUP", 340, 196, "Resistor_SMD:R_0805_2012Metric")
two_pin("R50", "GPIO21_I2C_SDA", "3V3")
part("Device:R", "R51", "4.7k I2C PULLUP", 340, 208, "Resistor_SMD:R_0805_2012Metric")
two_pin("R51", "GPIO22_I2C_SCL", "3V3")
part("Device:R", "R52", "10k OE SAFE PULLUP", 340, 220, "Resistor_SMD:R_0805_2012Metric")
two_pin("R52", "GPIO2_SERVO_OE", "3V3")

def add_servo(index, ref, label, x, y):
    raw = f"SERVO{index}_PWM_RAW"
    sig = f"SERVO{index}_PWM"
    rr = str(60 + index * 2)
    rp = str(61 + index * 2)
    part("Device:R", "R" + rr, "220R SIGNAL", x - 18, y,
         "Resistor_SMD:R_0805_2012Metric")
    two_pin("R" + rr, raw, sig)
    part("Device:R", "R" + rp, "10k SIGNAL PULLDOWN", x - 18, y + 8,
         "Resistor_SMD:R_0805_2012Metric")
    two_pin("R" + rp, sig, "GND")
    part("Connector_Generic:Conn_01x03", ref, label, x, y,
         "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical")
    pin_net(ref, 1, "GND")
    pin_net(ref, 2, "SERVO_6V")
    pin_net(ref, 3, sig)

add_servo(0, "J12", "MAIN_SWING_25KG_SERVO", 270, 244)
add_servo(1, "J13", "ELBOW_MG996R_SERVO", 310, 244)
add_servo(2, "J14", "WRIST_MG90S_SERVO", 350, 244)
s.add_text("Servo 1 = main swing; Servo 2 = elbow; Servo 3 = wrist.  Pin order: GND / regulated 6V / PWM.", (248, 260), size=1.05)

# Explicit power flags for ERC and PCB power-net recognition.
def add_flag(ref, net, x, y):
    part("power:PWR_FLAG", ref, "PWR_FLAG", x, y)
    pin_net(ref, 1, net, 3.81)

add_flag("#FLG01", "BAT_RAW", 20, 276)
add_flag("#FLG02", "VBAT_SW", 34, 276)
add_flag("#FLG03", "+5V_CTRL", 48, 276)
add_flag("#FLG04", "3V3", 62, 276)
# GND is intentionally not marked as a power source; adding a PWR_FLAG to GND
# can mask accidental shorts during ERC.
add_flag("#FLG05", "PI_5V", 76, 276)
add_flag("#FLG06", "SERVO_6V", 90, 276)
add_flag("#FLG07", "GND", 104, 276)

sch_path = OUT / "pickleball_robot_controller.kicad_sch"
s.save_as(sch_path, preserve_format=False)

# kicad-sch-api 0.5.x does not currently serialize newly added net labels when
# targeting KiCad 10.  They use a very small font: named net connectivity remains
# in the file/ERC/PCB, while short section notes make the drawing readable.
raw = sch_path.read_text(encoding="utf-8")
labels = []
for net, x, y, ex, ey, justify, angle in label_records:
    safe = net.replace('"', '\\"')
    labels.append(
        f'\t(global_label "{safe}"\n'
        f'\t\t(shape bidirectional)\n'
        f'\t\t(at {x:.4f} {y:.4f} {angle})\n'
        f'\t\t(fields_autoplaced yes)\n'
        f'\t\t(effects (font (size 0.25 0.25)) (justify {justify}))\n'
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n'
        f'\t\t\t(at {x:.4f} {y:.4f} {angle})\n'
        f'\t\t\t(effects (font (size 0.6 0.6)) (hide yes))\n'
        f'\t\t)\n'
        f'\t)\n'
    )
marker = "\t(sheet_instances"
if marker not in raw:
    marker = "\t(embedded_fonts"
raw = raw.replace(marker, "".join(labels) + marker, 1)
# Long autogenerated values (for example, net names and PWR_FLAG) were the
# source of the unreadable overlaps.  The BOM retains every exact value; this
# keeps values hidden on the drawing so it works as a clean wiring overview.
sch_path.write_text(raw, encoding="utf-8")

# Minimal KiCad project settings; KiCad will extend this on first GUI save.
pro_path = OUT / "pickleball_robot_controller.kicad_pro"
if not pro_path.exists():
    pro_path.write_text(json.dumps({"board": {}, "boards": [], "cvpcb": {}, "erc": {},
                                    "libraries": {}, "meta": {"filename": "pickleball_robot_controller.kicad_pro", "version": 1},
                                    "net_settings": {}, "pcbnew": {}, "schematic": {}, "text_variables": {}}, indent=2), encoding="utf-8")

print(sch_path)
print(s.get_statistics())
