"""Generate the real KiCad project as a readable six-sheet hierarchy."""
from pathlib import Path
import json
import re
import uuid
from kicad_sch_api import create_schematic

ROOT = Path(__file__).resolve().parent
TOTAL_SHEETS = 7

class Sheet:
    def __init__(self, filename, title, number):
        self.path = ROOT / filename
        self.s = create_schematic(filename.removesuffix(".kicad_sch"))
        self.s.set_paper_size("A3")
        self.s.set_title_block(title=title, date="2026-07-12", rev="R2-MULTISHEET",
                               company="Harrison", comments={1: f"Sheet {number} of {TOTAL_SHEETS}"})
        self.labels = []

    def part(self, lib, ref, value, x, y, footprint="", rotation=0.0):
        return self.s.components.add(lib, reference=ref, value=value,
                                     position=(x, y), footprint=footprint, rotation=rotation)

    def net(self, ref, pin, name, length=3.81):
        p = self.s.get_component_pin_position(ref, str(pin))
        comp=self.s.components.get(ref)
        c=comp.position
        rotation = round(comp.get_pin(str(pin)).rotation) % 360
        # Rotation chooses the pin axis; the pin's actual position relative to
        # the symbol centre chooses the outward direction. This works for tall
        # connectors as well as vertical passives without wiring through them.
        if rotation in (0,180):
            sign=-1 if p.x<c.x else 1
            end=(p.x+sign*length,p.y); angle=180 if sign<0 else 0; justify="right" if sign<0 else "left"
        else:
            sign=-1 if p.y<c.y else 1
            end=(p.x,p.y+sign*length); angle=270 if sign<0 else 90; justify="right" if sign<0 else "left"
        self.s.wires.add(start=(p.x,p.y), end=end)
        self.labels.append((name, end[0], end[1], angle, justify))

    def two(self, ref, a, b):
        self.net(ref, 1, a); self.net(ref, 2, b)

    def nc(self, ref, pin):
        self.s.no_connects.add(self.s.get_component_pin_position(ref, str(pin)))

    def text(self, value, x, y, size=1.5, bold=False):
        self.s.add_text(value, (x,y), size=size, bold=bold)

    def save(self):
        self.s.save_as(self.path, preserve_format=False)
        raw = self.path.read_text(encoding="utf-8")
        chunks=[]
        for name,x,y,angle,justify in self.labels:
            chunks.append(
                f'\t(global_label "{name}"\n\t\t(shape bidirectional)\n'
                f'\t\t(at {x:.4f} {y:.4f} {angle})\n'
                f'\t\t(fields_autoplaced yes)\n'
                f'\t\t(effects (font (size 0.9 0.9)) (justify {justify}))\n'
                f'\t\t(uuid "{uuid.uuid4()}")\n'
                f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n'
                f'\t\t\t(at {x:.4f} {y:.4f} {angle})\n'
                f'\t\t\t(effects (font (size 0.7 0.7)) (hide yes))\n\t\t)\n\t)\n')
        marker="\t(sheet_instances"
        raw=raw.replace(marker,"".join(chunks)+marker,1)
        self.path.write_text(raw,encoding="utf-8")

def flags(sh, entries, y=245):
    for i,(ref,net) in enumerate(entries):
        sh.part("power:PWR_FLAG",ref,"PWR_FLAG",25+i*25,y)
        sh.net(ref,1,net,5.08)

def testpoint(sh, ref, net, x, y, label=None):
    sh.part("Connector:TestPoint", ref, label or net, x, y,
            "TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm")
    sh.net(ref, 1, net, 5.08)

# ------------------------------------------------------------------ Sheet 1
p=Sheet("01_power_and_pi.kicad_sch","Battery Protection, Logic Buck, and Raspberry Pi Power",1)
p.text("BATTERY INPUT AND PROTECTION",65,18,2.2,True)
p.part("Connector_Generic:Conn_01x02","J1","XT60 PIGTAIL",35,38,"TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm")
p.net("J1",1,"BAT_RAW"); p.net("J1",2,"GND")
p.part("Device:Fuse","F1","15 A ATO BLADE",68,33,"Fuse:Fuse_Blade_ATO_directSolder"); p.two("F1","BAT_RAW","VBAT_SW")
p.part("Device:D_TVS","D1","SMBJ15A",100,38,"Diode_SMD:D_SMB"); p.two("D1","GND","VBAT_SW")
p.part("Device:C_Polarized","C1","1000 uF 35 V",128,38,"Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"); p.two("C1","VBAT_SW","GND")
p.part("Device:C","C2","1 uF 25 V",152,38,"Capacitor_SMD:C_0805_2012Metric"); p.two("C2","VBAT_SW","GND")
p.part("Connector_Generic:Conn_01x02","J18","EXTERNAL LATCHING E-STOP",185,38,"TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm")
p.net("J18",1,"VBAT_SW"); p.net("J18",2,"ACT_VBAT")
p.text("J18 must be closed by a latching E-stop switch. It removes actuator power but keeps Pi/ESP logic alive.",125,58,1.25)

p.text("BATTERY VOLTAGE MONITOR",65,78,1.8,True)
p.part("Device:R","R1","100 k 1%",45,98,"Resistor_SMD:R_0805_2012Metric"); p.two("R1","VBAT_SW","BAT_SENSE_RAW")
p.part("Device:R","R2","27 k 1%",80,98,"Resistor_SMD:R_0805_2012Metric"); p.two("R2","BAT_SENSE_RAW","GND")
p.part("Device:R","R3","1 k",115,98,"Resistor_SMD:R_0805_2012Metric"); p.two("R3","BAT_SENSE_RAW","GPIO33_BAT_ADC")
p.part("Device:C","C4","100 nF",150,98,"Capacitor_SMD:C_0805_2012Metric"); p.two("C4","GPIO33_BAT_ADC","GND")
p.part("Device:D_Schottky","D2","BAT54",175,88,"Diode_SMD:D_SOD-323"); p.two("D2","GND","GPIO33_BAT_ADC")
p.part("Device:D_Schottky","D14","BAT54",175,108,"Diode_SMD:D_SOD-323"); p.two("D14","GPIO33_BAT_ADC","3V3")

p.text("5 V CONTROL BUCK — ESP32 AND LOGIC ONLY",80,130,1.8,True)
p.part("Regulator_Switching:LM2596S-5","U1","LM2596S-5.0",70,158,"Package_TO_SOT_SMD:TO-263-5_TabPin3")
for pin,net in [(1,"VBAT_SW"),(2,"CTRL_SW"),(3,"GND"),(4,"+5V_CTRL"),(5,"GND")]: p.net("U1",pin,net)
p.part("Device:D_Schottky","D3","SS54",112,148,"Diode_SMD:D_SMA"); p.two("D3","GND","CTRL_SW")
p.part("Device:L","L1","33 uH 4 A",112,170,"Inductor_SMD:L_Sunlord_MWSA1265S"); p.two("L1","CTRL_SW","+5V_CTRL")
p.part("Device:C_Polarized","C5","220 uF 25 V",155,148,"Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"); p.two("C5","VBAT_SW","GND")
p.part("Device:C_Polarized","C7","330 uF 10 V",155,170,"Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"); p.two("C7","+5V_CTRL","GND")

p.text("RASPBERRY PI 5 V / 5 A BUCK",220,18,2.1,True)
p.part("Regulator_Switching:TPS54560BDDA","U4","TPS54560BDDA",265,58,"Package_SO:TI_SO-PowerPAD-8_ThermalVias")
for pin,net in [(1,"PI_BOOT"),(2,"VBAT_SW"),(3,"VBAT_SW"),(4,"PI_RT"),(5,"PI_FB"),(6,"PI_COMP"),(7,"GND"),(8,"PI_BUCK_SW"),(9,"GND")]: p.net("U4",pin,net)
p.part("Device:C","C31","100 nF",310,35,"Capacitor_SMD:C_0805_2012Metric"); p.two("C31","PI_BOOT","PI_BUCK_SW")
p.part("Device:D_Schottky","D9","B560C-13-F",310,58,"Diode_SMD:D_SMC"); p.two("D9","GND","PI_BUCK_SW")
p.part("Device:L","L2","XAL7070-682MEC 6.8 uH",350,58,"Inductor_SMD:L_Coilcraft_XAL7070-XXX"); p.two("L2","PI_BUCK_SW","PI_5V_RAW")
for i,ref in enumerate(["C32","C33","C34","C35"]):
    p.part("Device:C",ref,"2.2 uF 25 V",220+(i%2)*22,38+(i//2)*30,"Capacitor_SMD:C_0805_2012Metric"); p.two(ref,"VBAT_SW","GND")
p.part("Device:R","R30","243 k",230,100,"Resistor_SMD:R_0805_2012Metric"); p.two("R30","PI_RT","GND")
p.part("Device:R","R31","54.9 k 1%",300,100,"Resistor_SMD:R_0805_2012Metric"); p.two("R31","PI_5V_RAW","PI_FB")
p.part("Device:R","R32","10.2 k 1%",330,100,"Resistor_SMD:R_0805_2012Metric"); p.two("R32","PI_FB","GND")
p.part("Device:R","R33","16.9 k 1%",365,100,"Resistor_SMD:R_0805_2012Metric"); p.two("R33","PI_COMP","PI_COMP_RC")
p.part("Device:C","C36","5.1 nF",395,90,"Capacitor_SMD:C_0805_2012Metric"); p.two("C36","PI_COMP_RC","GND")
p.part("Device:C","C37","47 pF",395,110,"Capacitor_SMD:C_0805_2012Metric"); p.two("C37","PI_COMP","GND")
p.part("Device:C","C38","47 uF 10 V X7R",265,140,"Capacitor_SMD:C_1210_3225Metric"); p.two("C38","PI_5V_RAW","GND")
p.part("Device:C","C39","47 uF 10 V X7R",300,140,"Capacitor_SMD:C_1210_3225Metric"); p.two("C39","PI_5V_RAW","GND")
p.part("Device:C","C44","47 uF 10 V X7R",335,140,"Capacitor_SMD:C_1210_3225Metric"); p.two("C44","PI_5V_RAW","GND")
p.part("Device:Fuse","F3","5 A MINI BLADE",360,140,"Fuse:Fuseholder_Blade_Mini_Keystone_3568"); p.two("F3","PI_5V_RAW","PI_5V")
p.part("Connector_Generic:Conn_02x02_Odd_Even","J9","PI POWER OUT",385,165,"Connector_Molex:Molex_Mini-Fit_Jr_5569-04A2_2x02_P4.20mm_Horizontal")
for pin,net in [(1,"PI_5V"),(2,"PI_5V"),(3,"GND"),(4,"GND")]: p.net("J9",pin,net)
p.part("Device:C_Polarized","C30","470 uF 10 V LOW ESR",350,190,"Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"); p.two("C30","PI_5V","GND")
for ref,net,x,y in [("TP1","BAT_RAW",30,225),("TP2","VBAT_SW",75,225),("TP3","ACT_VBAT",120,225),
                    ("TP4","+5V_CTRL",165,225),("TP5","PI_5V",210,225),("TP6","GND",255,225)]:
    testpoint(p,ref,net,x,y)
flags(p,[("#FLG01","BAT_RAW"),("#FLG02","VBAT_SW"),("#FLG03","ACT_VBAT"),("#FLG04","PI_5V"),("#FLG05","GND")])
p.save()

# -------------------------------------------------------------- Sheet 2
c=Sheet("02_esp32_and_pi.kicad_sch","ESP32 Carrier, Raspberry Pi UART, and Status LEDs",2)
c.text("ESP32-PICO-KIT V4.1 CARRIER — CONFIRMED 17.78 mm ROW SPACING",100,18,2.0,True)
c.part("Connector_Generic:Conn_02x17_Odd_Even","J2","ESP32-PICO-KIT V4.1",85,100,"PickleballRobot:ESP32_PICO_KIT_V4_1_Carrier")
left=["GPIO21_I2C_SDA","GPIO22_I2C_SCL","GPIO19_PI_TX","GPIO23_LEFT_DIAG","GPIO18_PI_RX","GPIO5_RIGHT_DIAG",None,None,None,None,"GPIO35_ENC_LB","GPIO34_ENC_LA","GPIO38_ENC_RB","GPIO37_ENC_RA",None,"GND","3V3"]
right=["SENSOR_VP_GPIO36","SENSOR_VN_GPIO39","GPIO25_L_PWM","GPIO26_L_INA","GPIO32_SERVO_OE","GPIO33_BAT_ADC","GPIO27_L_INB","GPIO14_R_PWM",None,"GPIO13_R_INA",None,None,"GPIO4_R_INB",None,"3V3","GND","+5V_CTRL"]
for i,net in enumerate(left,1):
    if net:
        c.net("J2",2*i-1,net)
    else:
        c.nc("J2",2*i-1)
for i,net in enumerate(right,1): c.net("J2",2*i,net) if net else c.nc("J2",2*i)

c.text("RASPBERRY PI UART / CONTROL — NORMAL 2.54 mm HEADER",210,18,2.0,True)
c.part("Connector_Generic:Conn_01x08","J10","PI UART / CONTROL",255,72,"Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical")
jnets=["GND","GND","PI_TX_TO_ESP","ESP_TX_TO_PI","ACTUATOR_ENABLE","MOTOR_DIAG","PI_I2C_SDA","PI_I2C_SCL"]
for i,net in enumerate(jnets,1): c.net("J10",i,net) if net else c.nc("J10",i)
c.part("Device:R","R40","1 k",315,45,"Resistor_SMD:R_0805_2012Metric"); c.two("R40","PI_TX_TO_ESP","GPIO18_PI_RX")
c.part("Device:R","R41","1 k",315,65,"Resistor_SMD:R_0805_2012Metric"); c.two("R41","GPIO19_PI_TX","ESP_TX_TO_PI")
c.part("Device:R","R42","100 k DEFAULT OFF",315,85,"Resistor_SMD:R_0805_2012Metric"); c.two("R42","ACTUATOR_ENABLE","GND")
c.part("Device:R","R43","0 R DNP",315,105,"Resistor_SMD:R_0805_2012Metric"); c.two("R43","PI_I2C_SDA","GPIO21_I2C_SDA")
c.part("Device:R","R44","0 R DNP",315,125,"Resistor_SMD:R_0805_2012Metric"); c.two("R44","PI_I2C_SCL","GPIO22_I2C_SCL")
c.part("Connector_Generic:Conn_01x02","J20","ACTUATOR ENABLE OVERRIDE DNP",375,105,"Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
c.net("J20",1,"3V3"); c.net("J20",2,"ACTUATOR_ENABLE")
c.part("Device:R","R45","10 k",350,35,"Resistor_SMD:R_0805_2012Metric"); c.two("R45","MOTOR_DIAG","3V3")
c.part("Device:D","D15","1N4148",350,55,"Diode_SMD:D_SOD-323"); c.two("D15","MOTOR_DIAG","LEFT_DIAG")
c.part("Device:D","D16","1N4148",380,55,"Diode_SMD:D_SOD-323"); c.two("D16","MOTOR_DIAG","RIGHT_DIAG")
c.text("J10: 1/2 GND; 3 Pi TX->ESP GPIO18; 4 ESP GPIO19->Pi RX; 5 actuator enable; 6 fault; 7/8 I2C DNP.",205,145,1.15)
c.text("Pi: GPIO14 pin 8 -> J10.3; GPIO15 pin 10 <- J10.4; GPIO17 pin 11 -> J10.5; GND -> J10.1/2.",205,153,1.15)

c.text("STATUS LEDS",215,165,1.8,True)
leds=[("R100","D5","1 k","GREEN LOGIC","+5V_CTRL","LED_CTRL",220),
      ("R101","D6","1 k","BLUE PI","PI_5V","LED_PI",270),
      ("R102","D7","1 k","AMBER SERVO","SERVO_6V","LED_SERVO",320),
      ("R103","D8","1 k","RED FAULT","3V3","LED_FAULT",370)]
for rr,dd,rv,dv,a,m,x in leds:
    c.part("Device:R",rr,rv,x,190,"Resistor_SMD:R_0805_2012Metric"); c.two(rr,a,m)
    c.part("Device:LED",dd,dv,x,215,"LED_SMD:LED_0805_2012Metric"); c.two(dd,m,"MOTOR_DIAG" if dd=="D8" else "GND")
flags(c,[("#FLG07","3V3")],245)
for ref,net,x in [("TP7","3V3",210),("TP8","PI_TX_TO_ESP",245),("TP9","ESP_TX_TO_PI",280),
                  ("TP10","ACTUATOR_ENABLE",315),("TP11","MOTOR_DIAG",350),("TP12","GND",385)]:
    testpoint(c,ref,net,x,235)
c.save()

# ---------------------------------------------------------- motor sheet helper
def motor_sheet(filename,title,num,u,j,prefix,xgpio):
    m=Sheet(filename,title,num); m.text(title.upper(),70,18,2.2,True)
    m.part("Driver_Motor:VNH5019A-E",u,"VNH5019A-E",105,105,"PickleballRobot:VNH5019_MultiPowerSO30_ThermalVias")
    pwm,ina,inb,cs_adc,ea,eb=xgpio
    drv_pwm,drv_ina,drv_inb=[prefix+s for s in ("_PWM_DRV","_INA_DRV","_INB_DRV")]
    cs_raw=prefix+"_CS_RAW"; diag=prefix+"_DIAG"; diag_gpio=("GPIO23_LEFT_DIAG" if prefix=="LEFT" else "GPIO5_RIGHT_DIAG")
    branch=prefix+"_VBAT"
    fuse_ref="F5" if prefix=="LEFT" else "F6"
    m.part("Device:Fuse",fuse_ref,"5 A MINI BLADE MOTOR BRANCH",55,40,"Fuse:Fuseholder_Blade_Mini_Keystone_3568"); m.two(fuse_ref,"ACT_VBAT",branch)
    for pin,net in [(3,branch),(12,branch),(18,"GND"),(26,"GND"),(4,drv_ina),(10,drv_inb),(7,drv_pwm),(6,"GND"),(5,diag),(9,diag),(8,cs_raw),(1,prefix+"_OUTA"),(15,prefix+"_OUTB")]: m.net(u,pin,net)
    m.nc(u,11)
    m.part("Connector_Generic:Conn_01x06",j,prefix+" MOTOR + ENCODER",235,105,"Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical")
    # Exact cable order confirmed from the physical motor harness.
    for pin,net in [(1,prefix+"_OUTA"),(2,"GND"),(3,ea),(4,eb),(5,"ENC_3V3"),(6,prefix+"_OUTB")]: m.net(j,pin,net)
    pad_ref="J15" if prefix=="LEFT" else "J16"
    m.part("Connector_Generic:Conn_01x02",pad_ref,prefix+" MOTOR LARGE SOLDER PADS",300,105,
           "Connector_Wire:SolderWire-1.5sqmm_1x02_P7.8mm_D1.7mm_OD3.9mm")
    m.net(pad_ref,1,prefix+"_OUTA"); m.net(pad_ref,2,prefix+"_OUTB")
    cap="C12" if prefix=="LEFT" else "C15"; ccer="C13" if prefix=="LEFT" else "C16"; cbulk="C14" if prefix=="LEFT" else "C17"
    rcs="R7" if prefix=="LEFT" else "R14"; base=80 if prefix=="LEFT" else 90
    m.part("Device:C_Polarized",cap,"470 uF 35 V LOW ESR",175,45,"Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"); m.two(cap,branch,"GND")
    m.part("Device:C",ccer,"100 nF 50 V",205,40,"Capacitor_SMD:C_0805_2012Metric"); m.two(ccer,branch,"GND")
    m.part("Device:C",cbulk,"1 uF 25 V",205,62,"Capacitor_SMD:C_0805_2012Metric"); m.two(cbulk,branch,"GND")
    m.part("Device:R",rcs,"680 R current sense",175,145,"Resistor_SMD:R_0805_2012Metric"); m.two(rcs,cs_raw,"GND")
    for off,(gpio,drv) in enumerate([(pwm,drv_pwm),(ina,drv_ina),(inb,drv_inb)]):
        rs=f"R{base+off}"; rpd=f"R{base+3+off}"
        m.part("Device:R",rs,"1 k series",35,75+off*32,"Resistor_SMD:R_0805_2012Metric"); m.two(rs,gpio,drv)
        m.part("Device:R",rpd,"10 k pulldown",65,75+off*32,"Resistor_SMD:R_0805_2012Metric"); m.two(rpd,drv,"GND")
    rdiag=f"R{base+6}"; rdiagser=f"R{base+9}"
    m.part("Device:R",rdiag,"10 k fault pullup",45,180,"Resistor_SMD:R_0805_2012Metric"); m.two(rdiag,diag,"3V3")
    m.part("Device:R",rdiagser,"1 k diag series",80,180,"Resistor_SMD:R_0805_2012Metric"); m.two(rdiagser,diag,diag_gpio)
    radc=f"R{base+8}"; m.part("Device:R",radc,"4.7 k ADC protect",175,170,"Resistor_SMD:R_0805_2012Metric"); m.two(radc,cs_raw,cs_adc)
    cc=f"C{base}"; m.part("Device:C",cc,"10 nF current filter",205,185,"Capacitor_SMD:C_0805_2012Metric"); m.two(cc,cs_adc,"GND")
    dlo="D17" if prefix=="LEFT" else "D19"; dhi="D18" if prefix=="LEFT" else "D20"
    m.part("Device:D_Schottky",dlo,"BAT54",240,170,"Diode_SMD:D_SOD-323"); m.two(dlo,"GND",cs_adc)
    m.part("Device:D_Schottky",dhi,"BAT54",240,190,"Diode_SMD:D_SOD-323"); m.two(dhi,cs_adc,"3V3")
    motor_cap="C18" if prefix=="LEFT" else "C19"
    m.part("Device:C",motor_cap,"100 nF 50 V FIT AT MOTOR",300,155,""); m.two(motor_cap,prefix+"_OUTA",prefix+"_OUTB")
    m.text("J4/J5 cable: 1 RED motor+; 2 BLACK encoder GND; 3 YELLOW encoder A; 4 GREEN encoder B; 5 BLUE encoder +3V3; 6 WHITE motor-.",200,215,1.25)
    m.text(f"{pad_ref}: large 1.7 mm through-holes in parallel with pins 1/6 for separately soldered red and white motor-power wires.",200,225,1.25)
    tpbase=20 if prefix=="LEFT" else 30
    for off,(net,label) in enumerate([(branch,"VBAT"),(drv_pwm,"PWM"),(drv_ina,"INA"),(drv_inb,"INB"),(diag,"DIAG"),(cs_adc,"CS ADC"),(ea,"ENC A"),(eb,"ENC B"),("GND","GND")]):
        testpoint(m,f"TP{tpbase+off}",net,25+off*42,245,label)
    flags(m,[("#FLG09" if prefix=="LEFT" else "#FLG10",branch)],260)
    m.save()

motor_sheet("03_left_motor.kicad_sch","Left Wheel Motor Driver",3,"U2","J4","LEFT",("GPIO25_L_PWM","GPIO26_L_INA","GPIO27_L_INB","SENSOR_VP_GPIO36","LEFT_ENC_A_CABLE","LEFT_ENC_B_CABLE"))
motor_sheet("04_right_motor.kicad_sch","Right Wheel Motor Driver",4,"U3","J5","RIGHT",("GPIO14_R_PWM","GPIO13_R_INA","GPIO4_R_INB","SENSOR_VN_GPIO39","RIGHT_ENC_A_CABLE","RIGHT_ENC_B_CABLE"))

# -------------------------------------------------------------- Sheet 5
e=Sheet("05_encoder_inputs.kicad_sch","Wheel Encoder Input Conditioning",5)
e.text("FOUR 3.3 V SCHMITT-BUFFERED ENCODER INPUTS",95,18,2.1,True)
e.part("Device:FerriteBead","FB1","BLM21PG221SN1D 220R@100MHz",45,45,"Inductor_SMD:L_0805_2012Metric"); e.two("FB1","3V3","ENC_3V3")
e.part("Device:C","C84","10 uF 10 V",80,38,"Capacitor_SMD:C_0805_2012Metric"); e.two("C84","ENC_3V3","GND")
e.part("Device:C","C85","100 nF",80,58,"Capacitor_SMD:C_0805_2012Metric"); e.two("C85","ENC_3V3","GND")
channels=[("U6",55,"LEFT_ENC_A_CABLE","LEFT_ENC_A_RAW","GPIO34_ENC_LA"),("U7",145,"LEFT_ENC_B_CABLE","LEFT_ENC_B_RAW","GPIO35_ENC_LB"),("U8",235,"RIGHT_ENC_A_CABLE","RIGHT_ENC_A_RAW","GPIO37_ENC_RA"),("U9",325,"RIGHT_ENC_B_CABLE","RIGHT_ENC_B_RAW","GPIO38_ENC_RB")]
for idx,(u,x,cable,raw,out) in enumerate(channels):
    rs=f"R{72+idx}"; e.part("Device:R",rs,"1 k cable protection",x,70,"Resistor_SMD:R_0805_2012Metric"); e.two(rs,cable,raw)
    e.part("74xGxx:74LVC1G14",u,"74LVC1G14",x,100,"Package_TO_SOT_SMD:SOT-23-5")
    e.nc(u,1); e.net(u,2,raw); e.net(u,3,"GND"); e.net(u,4,out); e.net(u,5,"3V3")
    rr=f"R{76+idx}"; cc=f"C{76+idx}"
    e.part("Device:R",rr,"10 k pullup",x,150,"Resistor_SMD:R_0805_2012Metric"); e.two(rr,raw,"3V3")
    e.part("Device:C",cc,"1 nF filter",x,190,"Capacitor_SMD:C_0805_2012Metric"); e.two(cc,raw,"GND")
    cd=f"C{86+idx}"; e.part("Device:C",cd,"100 nF local bypass",x+30,115,"Capacitor_SMD:C_0805_2012Metric"); e.two(cd,"3V3","GND")
e.text("The six-pin J4/J5 connectors are on the motor-driver sheets; their encoder A/B pins enter here.",185,220,1.4)
for idx,(net,label) in enumerate([("ENC_3V3","ENC 3V3"),("LEFT_ENC_A_RAW","L A RAW"),("GPIO34_ENC_LA","L A OUT"),
                                  ("LEFT_ENC_B_RAW","L B RAW"),("GPIO35_ENC_LB","L B OUT"),("RIGHT_ENC_A_RAW","R A RAW"),
                                  ("GPIO37_ENC_RA","R A OUT"),("RIGHT_ENC_B_RAW","R B RAW"),("GPIO38_ENC_RB","R B OUT"),("GND","GND")]):
    testpoint(e,f"TP{40+idx}",net,25+idx*38,245,label)
e.save()

# -------------------------------------------------------------- Sheet 6
s=Sheet("06_arm_servos.kicad_sch","Servo Power Regulator and 3-DOF Arm Control",6)
s.text("6 V / 5 A SERVO BUCK",65,18,2.1,True)
s.part("Regulator_Switching:TPS54560BDDA","U10","TPS54560BDDA",70,65,"Package_SO:TI_SO-PowerPAD-8_ThermalVias")
for pin,net in [(1,"SERVO_BOOT"),(2,"ACT_VBAT"),(3,"ACTUATOR_ENABLE"),(4,"SERVO_RT"),(5,"SERVO_FB"),(6,"SERVO_COMP"),(7,"GND"),(8,"SERVO_BUCK_SW"),(9,"GND")]: s.net("U10",pin,net)
s.part("Device:C","C45","100 nF",115,38,"Capacitor_SMD:C_0805_2012Metric"); s.two("C45","SERVO_BOOT","SERVO_BUCK_SW")
s.part("Device:D_Schottky","D10","B560C-13-F",115,65,"Diode_SMD:D_SMC"); s.two("D10","GND","SERVO_BUCK_SW")
s.part("Device:L","L3","XAL7070-682MEC 6.8 uH",155,65,"Inductor_SMD:L_Coilcraft_XAL7070-XXX"); s.two("L3","SERVO_BUCK_SW","SERVO_6V_RAW")
for i,ref in enumerate(["C46","C47","C64","C65"]): s.part("Device:C",ref,"2.2 uF 25 V",25+(i%2)*25,95+(i//2)*25,"Capacitor_SMD:C_0805_2012Metric"); s.two(ref,"ACT_VBAT","GND")
s.part("Device:R","R104","243 k",90,115,"Resistor_SMD:R_0805_2012Metric"); s.two("R104","SERVO_RT","GND")
s.part("Device:R","R105","66.3 k 1%",125,115,"Resistor_SMD:R_0805_2012Metric"); s.two("R105","SERVO_6V_RAW","SERVO_FB")
s.part("Device:R","R106","10.2 k 1%",160,115,"Resistor_SMD:R_0805_2012Metric"); s.two("R106","SERVO_FB","GND")
s.part("Device:R","R107","18.2 k 1%",195,115,"Resistor_SMD:R_0805_2012Metric"); s.two("R107","SERVO_COMP","SERVO_COMP_RC")
s.part("Device:C","C48","5.6 nF",230,105,"Capacitor_SMD:C_0805_2012Metric"); s.two("C48","SERVO_COMP_RC","GND")
s.part("Device:C","C49","47 pF",230,130,"Capacitor_SMD:C_0805_2012Metric"); s.two("C49","SERVO_COMP","GND")
s.part("Device:C","C50","47 uF 10 V X7R",270,45,"Capacitor_SMD:C_1210_3225Metric"); s.two("C50","SERVO_6V_RAW","GND")
s.part("Device:C","C51","47 uF 10 V X7R",270,70,"Capacitor_SMD:C_1210_3225Metric"); s.two("C51","SERVO_6V_RAW","GND")
s.part("Device:C","C62","47 uF 10 V X7R",270,95,"Capacitor_SMD:C_1210_3225Metric"); s.two("C62","SERVO_6V_RAW","GND")
s.part("Device:Fuse","F2","5 A MINI BLADE SERVO",305,65,"Fuse:Fuseholder_Blade_Mini_Keystone_3568"); s.two("F2","SERVO_6V_RAW","SERVO_6V")
s.part("Device:D_TVS","D4","SMBJ8.0A",340,55,"Diode_SMD:D_SMB"); s.two("D4","GND","SERVO_6V")
s.part("Device:C_Polarized","C40","470 uF 10 V LOW ESR",370,55,"Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"); s.two("C40","SERVO_6V","GND")
s.part("Connector_Generic:Conn_01x02","J11","SERVO 6 V TEST/OUT",350,100,"TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm"); s.net("J11",1,"SERVO_6V"); s.net("J11",2,"GND")

s.text("PCA9685 SERVO PWM CONTROL",75,165,2.0,True)
s.part("Driver_LED:PCA9685PW","U5","PCA9685PW",100,215,"Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm")
for pin in [1,2,3,4,5,14,24,25]: s.net("U5",pin,"GND")
for pin,net in [(28,"3V3"),(26,"GPIO22_I2C_SCL"),(27,"GPIO21_I2C_SDA"),(23,"GPIO32_SERVO_OE"),(6,"SERVO0_PWM_RAW"),(7,"SERVO1_PWM_RAW"),(8,"SERVO2_PWM_RAW")]: s.net("U5",pin,net)
for pin in range(9,23):
    if pin not in [14]: s.nc("U5",pin)
s.part("Device:C","C42","100 nF",160,185,"Capacitor_SMD:C_0805_2012Metric"); s.two("C42","3V3","GND")
s.part("Device:C","C43","10 uF 10 V",160,210,"Capacitor_SMD:C_0805_2012Metric"); s.two("C43","3V3","GND")
s.part("Device:R","R50","4.7 k",195,185,"Resistor_SMD:R_0805_2012Metric"); s.two("R50","GPIO21_I2C_SDA","3V3")
s.part("Device:R","R51","4.7 k",195,210,"Resistor_SMD:R_0805_2012Metric"); s.two("R51","GPIO22_I2C_SCL","3V3")
s.part("Device:R","R52","10 k DEFAULT DISABLED",195,235,"Resistor_SMD:R_0805_2012Metric"); s.two("R52","GPIO32_SERVO_OE","3V3")
def servo(idx,ref,label,x,power_net="SERVO_6V"):
    raw=f"SERVO{idx}_PWM_RAW"; sig=f"SERVO{idx}_PWM"; rser=f"R{60+idx*2}"; rpd=f"R{61+idx*2}"
    s.part("Device:R",rser,"220 R",x,185,"Resistor_SMD:R_0805_2012Metric"); s.two(rser,raw,sig)
    s.part("Device:R",rpd,"10 k pulldown",x,215,"Resistor_SMD:R_0805_2012Metric"); s.two(rpd,sig,"GND")
    s.part("Connector_Generic:Conn_01x03",ref,label,x,255,"Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
    s.net(ref,1,"GND"); s.net(ref,2,power_net); s.net(ref,3,sig)
servo(0,"J12","MIUZEI 25KG 270 DEG",255,"MAIN_SERVO_8V4"); servo(1,"J13","ELBOW MG996R",315); servo(2,"J14","WRIST MG90S",375)
s.text("Header order: pin 1 GND, pin 2 power, pin 3 PWM. J12 = 8.4 V; J13/J14 = 6 V.",225,238,1.3)
flags(s,[("#FLG06","SERVO_6V")],245)
for ref,net,x in [("TP50","ACT_VBAT",25),("TP51","ACTUATOR_ENABLE",75),("TP52","SERVO_6V",125),
                  ("TP53","GPIO21_I2C_SDA",175),("TP54","GPIO22_I2C_SCL",225),("TP55","GPIO32_SERVO_OE",275),("TP56","GND",325)]:
    testpoint(s,ref,net,x,145)
s.save()

# -------------------------------------------------------------- Sheet 7
h=Sheet("07_main_servo_8v4.kicad_sch","Miuzei Main-Swing Servo 8.4 V Power Rail",7)
h.text("DEDICATED 8.4 V / 5 A BUCK FOR MIUZEI 25KG 270 DEG SERVO",120,18,2.0,True)
h.part("Regulator_Switching:TPS54560BDDA","U11","TPS54560BDDA",95,75,"Package_SO:TI_SO-PowerPAD-8_ThermalVias")
for pin,net in [(1,"MAIN8_BOOT"),(2,"ACT_VBAT"),(3,"ACTUATOR_ENABLE"),(4,"MAIN8_RT"),(5,"MAIN8_FB"),(6,"MAIN8_COMP"),(7,"GND"),(8,"MAIN8_SW"),(9,"GND")]: h.net("U11",pin,net)
h.part("Device:C","C52","100 nF",145,42,"Capacitor_SMD:C_0805_2012Metric"); h.two("C52","MAIN8_BOOT","MAIN8_SW")
h.part("Device:D_Schottky","D11","B560C-13-F",145,75,"Diode_SMD:D_SMC"); h.two("D11","GND","MAIN8_SW")
h.part("Device:L","L4","XAL7070-682MEC 6.8 uH",195,75,"Inductor_SMD:L_Coilcraft_XAL7070-XXX"); h.two("L4","MAIN8_SW","MAIN8_RAW")
for i,ref in enumerate(["C53","C54","C55","C56"]):
    h.part("Device:C",ref,"2.2 uF 25 V",30+(i%2)*25,60+(i//2)*35,"Capacitor_SMD:C_0805_2012Metric"); h.two(ref,"ACT_VBAT","GND")
h.part("Device:R","R108","243 k",70,135,"Resistor_SMD:R_0805_2012Metric"); h.two("R108","MAIN8_RT","GND")
h.part("Device:R","R109","96.9 k 1%",120,135,"Resistor_SMD:R_0805_2012Metric"); h.two("R109","MAIN8_RAW","MAIN8_FB")
h.part("Device:R","R110","10.2 k 1%",165,135,"Resistor_SMD:R_0805_2012Metric"); h.two("R110","MAIN8_FB","GND")
h.part("Device:R","R111","17.8 k 1%",210,135,"Resistor_SMD:R_0805_2012Metric"); h.two("R111","MAIN8_COMP","MAIN8_COMP_RC")
h.part("Device:C","C57","5.6 nF",250,120,"Capacitor_SMD:C_0805_2012Metric"); h.two("C57","MAIN8_COMP_RC","GND")
h.part("Device:C","C58","47 pF",250,150,"Capacitor_SMD:C_0805_2012Metric"); h.two("C58","MAIN8_COMP","GND")
for i,ref in enumerate(["C59","C60","C63","C66"]):
    h.part("Device:C",ref,"22 uF 25 V X7R",280+(i%2)*28,50+(i//2)*30,"Capacitor_SMD:C_1210_3225Metric"); h.two(ref,"MAIN8_RAW","GND")
h.part("Device:Fuse","F4","5 A MINI BLADE MAIN SERVO",330,75,"Fuse:Fuseholder_Blade_Mini_Keystone_3568"); h.two("F4","MAIN8_RAW","MAIN_SERVO_8V4")
h.part("Device:D_TVS","D12","SMBJ10A",370,60,"Diode_SMD:D_SMB"); h.two("D12","GND","MAIN_SERVO_8V4")
h.part("Device:C_Polarized","C61","220 uF 16 V LOW ESR",370,100,"Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"); h.two("C61","MAIN_SERVO_8V4","GND")
h.part("Connector_Generic:Conn_01x02","J17","8.4 V TEST / AUX OUT",330,145,"TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm"); h.net("J17",1,"MAIN_SERVO_8V4"); h.net("J17",2,"GND")
h.part("Device:R","R112","2.2 k",300,190,"Resistor_SMD:R_0805_2012Metric"); h.two("R112","MAIN_SERVO_8V4","LED_MAIN8")
h.part("Device:LED","D13","PURPLE 8.4 V",350,190,"LED_SMD:LED_0805_2012Metric"); h.two("D13","LED_MAIN8","GND")
h.text("U11 uses 96.9 k / 10.2 k feedback resistors for approximately 8.40 V. J12 is the only servo powered from this rail.",180,210,1.3)
h.text("J13 MG996R and J14 MG90S remain on the separate regulated 6 V rail.",145,220,1.3)
flags(h,[("#FLG08","MAIN_SERVO_8V4")],245)
for ref,net,x in [("TP60","ACT_VBAT",50),("TP61","ACTUATOR_ENABLE",110),("TP62","MAIN_SERVO_8V4",180),("TP63","GND",260)]:
    testpoint(h,ref,net,x,170)
h.save()

# --------------------------------------------------------------- root sheet
root=create_schematic("pickleball_robot_controller")
root.set_paper_size("A4")
root.set_title_block(title="Pickleball Robot Controller — Hierarchical Overview",date="2026-07-12",rev="R2-MULTISHEET",company="Harrison")
root.add_text("PICKLEBALL ROBOT CONTROLLER — SEVEN READABLE KICAD SHEETS",(25,20),size=2.2,bold=True)
sheet_defs=[
    ("01 Power and Pi","01_power_and_pi.kicad_sch",(25,40)),
    ("02 ESP32 and Pi UART","02_esp32_and_pi.kicad_sch",(120,40)),
    ("03 Left Motor","03_left_motor.kicad_sch",(25,90)),
    ("04 Right Motor","04_right_motor.kicad_sch",(120,90)),
    ("05 Encoders","05_encoder_inputs.kicad_sch",(25,140)),
    ("06 Arm Servos","06_arm_servos.kicad_sch",(120,140)),
    ("07 Main Servo 8.4V","07_main_servo_8v4.kicad_sch",(72,185)),
]
sheet_ids=[]
for i,(name,file,pos) in enumerate(sheet_defs,1):
    sheet_ids.append(root.add_sheet(name,file,pos,(70,28),project_name="pickleball_robot_controller",page_number=str(i+1)))
root.add_text("Global net labels connect the sheets. Open any sheet from the hierarchy panel.",(35,225),size=1.3)
root.save_as(ROOT/"pickleball_robot_controller.kicad_sch",preserve_format=False)

# kicad-sch-api creates each child as a standalone project. Re-home every child
# instance path under the root/sheet UUID so KiCad treats the six files as six
# distinct hierarchy pages rather than overlaying their coordinates/nets.
root_raw=(ROOT/"pickleball_robot_controller.kicad_sch").read_text(encoding="utf-8")
root_uuid=re.search(r'\(uuid "([0-9a-f-]+)"\)',root_raw).group(1)
for page,((name,file,pos),sheet_uuid) in enumerate(zip(sheet_defs,sheet_ids),2):
    child_path=ROOT/file
    raw=child_path.read_text(encoding="utf-8")
    child_uuid=re.search(r'\(uuid "([0-9a-f-]+)"\)',raw).group(1)
    raw=raw.replace(f'(project "{Path(file).stem}"', '(project "pickleball_robot_controller"')
    raw=raw.replace(f'(path "/{child_uuid}"',f'(path "/{root_uuid}/{sheet_uuid}"')
    raw=raw.replace('(sheet_instances\n\t\t(path "/"',f'(sheet_instances\n\t\t(path "/{root_uuid}/{sheet_uuid}"')
    raw=raw.replace('(page "1")\n\t\t)\n\t)\n\t(embedded_fonts',f'(page "{page}")\n\t\t)\n\t)\n\t(embedded_fonts')
    child_path.write_text(raw,encoding="utf-8")

pro=ROOT/"pickleball_robot_controller.kicad_pro"
if not pro.exists():
    pro.write_text(json.dumps({"board":{},"boards":[],"cvpcb":{},"erc":{},"libraries":{},"meta":{"filename":pro.name,"version":1},"net_settings":{},"pcbnew":{},"schematic":{},"text_variables":{}},indent=2),encoding="utf-8")
print("Generated root and seven KiCad schematic sheets")
