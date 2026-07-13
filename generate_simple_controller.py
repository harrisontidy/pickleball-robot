"""Generate the intentionally simple hobby controller KiCad project."""
from pathlib import Path
import json, re, uuid
from kicad_sch_api import create_schematic

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "simple_hobby_controller"
OUT.mkdir(exist_ok=True)

class Sheet:
    def __init__(self, filename, title, page):
        self.path = OUT / filename
        self.s = create_schematic(filename.removesuffix(".kicad_sch"))
        self.s.set_paper_size("A3")
        self.s.set_title_block(title=title, date="2026-07-12", rev="H1-SIMPLE",
                               company="Harrison", comments={1: f"Page {page} - hobby/debuggable version"})
        self.labels=[]; self.horizontal_refs=set()

    def part(self, lib, ref, value, x, y, footprint="", rotation=0.0):
        # KiCad's two-pin device symbols are vertical at 0 degrees.  Keeping
        # them horizontal makes the labels read left-to-right with no stacks.
        if rotation == 0.0 and lib in {"Device:R","Device:C","Device:C_Polarized","Device:Fuse"}:
            rotation = 90.0
            self.horizontal_refs.add(ref)
        return self.s.components.add(lib, reference=ref, value=value,
                                     position=(x,y), footprint=footprint, rotation=rotation)

    def net(self, ref, pin, name, length=3.81):
        p=self.s.get_component_pin_position(ref,str(pin)); c=self.s.components.get(ref).position
        # Use the pin's actual geometry after rotation.  The library pin
        # rotation field itself is not transformed with the component and
        # previously made labels on horizontal resistors turn vertical.
        rot=round(self.s.components.get(ref).get_pin(str(pin)).rotation)%360
        horizontal = (abs(p.x-c.x) >= abs(p.y-c.y)) if ref in self.horizontal_refs else rot in (0,180)
        if horizontal:
            sign=-1 if p.x<c.x else 1; end=(p.x+sign*length,p.y); angle=180 if sign<0 else 0; just="right" if sign<0 else "left"
        else:
            sign=-1 if p.y<c.y else 1; end=(p.x,p.y+sign*length); angle=270 if sign<0 else 90; just="right" if sign<0 else "left"
        self.s.wires.add(start=(p.x,p.y),end=end); self.labels.append((name,*end,angle,just))

    def two(self, ref, a, b): self.net(ref,1,a); self.net(ref,2,b)
    def nc(self,ref,pin): self.s.no_connects.add(self.s.get_component_pin_position(ref,str(pin)))
    def text(self,t,x,y,size=1.35,bold=False): self.s.add_text(t,(x,y),size=size,bold=bold)

    def save(self):
        tmp=self.path.with_suffix(".generated.kicad_sch"); self.s.save_as(tmp,preserve_format=False)
        raw=tmp.read_text(encoding="utf-8"); blocks=[]
        for name,x,y,angle,just in self.labels:
            blocks.append(f'\t(global_label "{name}"\n\t\t(shape bidirectional)\n\t\t(at {x:.4f} {y:.4f} {angle})\n\t\t(fields_autoplaced yes)\n\t\t(effects (font (size 1.0 1.0)) (justify {just}))\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:.4f} {y:.4f} {angle}) (effects (font (size 0.7 0.7)) (hide yes)))\n\t)\n')
        raw=raw.replace("\t(sheet_instances","".join(blocks)+"\t(sheet_instances",1)
        self.path.write_text(raw,encoding="utf-8"); tmp.unlink()

R0805="Resistor_SMD:R_0805_2012Metric"; C0805="Capacitor_SMD:C_0805_2012Metric"

# Page 1: connectors, power, and the single dual H-bridge.
p=Sheet("simple_01_power_motors.kicad_sch","Simple Power and Dual Wheel Driver",2)
p.text("POWER INPUTS",45,20,2.0,True)
p.part("Connector_Generic:Conn_01x02","J1","3S BATTERY XT60",45,52,"Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal")
p.net("J1",1,"VBAT_3S"); p.net("J1",2,"GND")
p.part("Device:Fuse","F1","3 A MINI BLADE - CHANGE AFTER STALL TEST",85,42,"Fuse:Fuseholder_Blade_Mini_Keystone_3568"); p.two("F1","VBAT_3S","MOTOR_VM")
p.part("Device:C_Polarized","C1","470 uF 25 V MOTOR BULK",125,42,"Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"); p.two("C1","MOTOR_VM","GND")
p.part("Device:C","C2","100 nF 25 V",155,42,C0805); p.two("C2","MOTOR_VM","GND")
p.part("Connector_Generic:Conn_01x02","J2","REGULATED 5 V INPUT XT30",45,92,"Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal")
p.net("J2",1,"+5V"); p.net("J2",2,"GND")
p.part("Device:C_Polarized","C3","1000 uF 10 V SERVO BULK",90,82,"Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"); p.two("C3","+5V","GND")
p.part("Device:C","C4","100 nF",125,82,C0805); p.two("C4","+5V","GND")
p.text("J2 MUST receive regulated 5 V from an external 5-8 A RC UBEC. Never connect the 3S battery directly to J2.",170,118,1.25)

p.text("ONE DUAL H-BRIDGE",260,20,2.0,True)
p.part("Driver_Motor:DRV8848","U1","DRV8848PWP",260,82,"Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask3x3mm_ThermalVias")
for pin,net in [(1,"3V3"),(2,"LEFT_OUT_A"),(3,"GND"),(4,"LEFT_OUT_B"),(5,"RIGHT_OUT_B"),(6,"GND"),(7,"RIGHT_OUT_A"),(8,"MOTOR_FAULT"),(9,"MOTOR_BIN1"),(10,"MOTOR_BIN2"),(11,"DRV_VINT"),(12,"MOTOR_VM"),(13,"GND"),(14,"DRV_VINT"),(15,"MOTOR_AIN2"),(16,"MOTOR_AIN1"),(17,"GND")]: p.net("U1",pin,net)
p.part("Device:C","C5","470 nF VINT",315,37,C0805); p.two("C5","DRV_VINT","GND")
p.part("Device:R","R1","10 k FAULT PULLUP",350,37,R0805); p.two("R1","MOTOR_FAULT","3V3")
p.part("power:PWR_FLAG","#FLG01","PWR_FLAG",180,82); p.net("#FLG01",1,"MOTOR_VM")
p.part("power:PWR_FLAG","#FLG02","PWR_FLAG",180,102); p.net("#FLG02",1,"GND")
for i,(net,x,y) in enumerate([("MOTOR_AIN1",215,135),("MOTOR_AIN2",250,135),("MOTOR_BIN1",285,135),("MOTOR_BIN2",320,135)],1):
    p.part("Device:R",f"R{i+1}","10 k STARTUP PULLDOWN",x,y,R0805); p.two(f"R{i+1}",net,"GND")
p.text("DRV8848 contains both H-bridges, flyback paths, thermal shutdown, undervoltage and overcurrent protection.",205,165,1.25)

def motor(ref,label,x,outa,outb,ea,eb):
    p.part("Connector_Generic:Conn_01x06",ref,label,x,210,"Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical")
    for pin,net in [(1,outa),(2,"GND"),(3,ea),(4,eb),(5,"3V3"),(6,outb)]: p.net(ref,pin,net)
motor("J3","LEFT GA25-370 - JST PH 2.0 mm",90,"LEFT_OUT_A","LEFT_OUT_B","LEFT_ENC_A","LEFT_ENC_B")
motor("J4","RIGHT GA25-370 - JST PH 2.0 mm",225,"RIGHT_OUT_A","RIGHT_OUT_B","RIGHT_ENC_A","RIGHT_ENC_B")
p.text("MOTOR CABLE ORDER: 1 red motor; 2 black encoder GND; 3 yellow encoder A; 4 green encoder B; 5 blue encoder 3.3 V; 6 white motor.",205,265,1.25)
p.part("Connector_Generic:Conn_01x02","J5","LEFT MOTOR LARGE SOLDER PADS",340,205,"Connector_Wire:SolderWire-1.5sqmm_1x02_P7.8mm_D1.7mm_OD3.9mm"); p.net("J5",1,"LEFT_OUT_A"); p.net("J5",2,"LEFT_OUT_B")
p.part("Connector_Generic:Conn_01x02","J6","RIGHT MOTOR LARGE SOLDER PADS",340,240,"Connector_Wire:SolderWire-1.5sqmm_1x02_P7.8mm_D1.7mm_OD3.9mm"); p.net("J6",1,"RIGHT_OUT_A"); p.net("J6",2,"RIGHT_OUT_B")
p.save()

# Page 2: ESP carrier, direct servo PWM, encoders, and UART only.
c=Sheet("simple_02_esp_servos_uart.kicad_sch","ESP32, Three Servos, Encoders, and Pi UART",3)
c.text("ESP32-PICO-KIT V4.1 CARRIER",80,20,2.0,True)
c.part("Connector_Generic:Conn_02x17_Odd_Even","J7","ESP32-PICO-KIT V4.1",95,105,"PickleballRobot:ESP32_PICO_KIT_V4_1_Carrier")
left=[None,"MOTOR_FAULT","ESP_TX_TO_PI","MOTOR_BIN2","PI_TX_TO_ESP",None,None,None,None,None,"GPIO35","GPIO34","GPIO38","GPIO37",None,"GND","3V3"]
right=[None,None,"SERVO1_PWM","SERVO2_PWM",None,None,"SERVO3_PWM","MOTOR_BIN1",None,"MOTOR_AIN1",None,None,"MOTOR_AIN2",None,"3V3","GND","+5V"]
for i,n in enumerate(left,1): c.net("J7",2*i-1,n) if n else c.nc("J7",2*i-1)
for i,n in enumerate(right,1): c.net("J7",2*i,n) if n else c.nc("J7",2*i)

c.text("THREE INDEPENDENT 5 V SERVOS",245,20,2.0,True)
for idx,(ref,name,x,pwm) in enumerate([("J8","MAIN SWING SERVO",220,"SERVO1_PWM"),("J9","ELBOW SERVO",285,"SERVO2_PWM"),("J10","WRIST SERVO",350,"SERVO3_PWM")]):
    c.part("Connector_Generic:Conn_01x03",ref,name,x,65,"Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
    c.net(ref,1,"GND"); c.net(ref,2,"+5V"); c.net(ref,3,f"{pwm}_PIN")
    c.part("Device:R",f"R{10+idx}","220 R PWM SERIES",x,105,R0805); c.two(f"R{10+idx}",pwm,f"{pwm}_PIN")
    c.part("Device:R",f"R{13+idx}","10 k PWM PULLDOWN",x,135,R0805); c.two(f"R{13+idx}",f"{pwm}_PIN","GND")
c.text("Servo headers: pin 1 GND, pin 2 regulated +5 V, pin 3 separate PWM. Each servo moves independently.",205,165,1.25)

c.text("ENCODER INPUTS",70,205,1.8,True)
for idx,(raw,gpio,x) in enumerate([("LEFT_ENC_A","GPIO34",40),("LEFT_ENC_B","GPIO35",90),("RIGHT_ENC_A","GPIO37",140),("RIGHT_ENC_B","GPIO38",190)]):
    c.part("Device:R",f"R{20+idx}","1 k SERIES",x,230,R0805); c.two(f"R{20+idx}",raw,gpio)
    c.part("Device:R",f"R{24+idx}","10 k PULLUP",x,260,R0805); c.two(f"R{24+idx}",raw,"3V3")
c.text("Motor encoder outputs are assumed 3.3 V because their blue supply wire is powered from 3.3 V.",125,285,1.15)

c.text("RASPBERRY PI 3.3 V UART",300,205,1.8,True)
c.part("Connector_Generic:Conn_01x04","J11","PI UART - 2.54 mm HEADER",300,240,"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
for pin,net in [(1,"GND"),(2,"PI_TX_TO_ESP"),(3,"ESP_TX_TO_PI"),(4,"3V3")]: c.net("J11",pin,net)
c.text("J11: 1 GND; 2 Pi TX -> ESP GPIO18 RX; 3 ESP GPIO19 TX -> Pi RX; 4 is 3.3 V reference only.",245,275,1.15)
c.text("DO NOT power the Raspberry Pi from J11. Power the Pi from its own proper 5 V supply/USB-C regulator.",245,285,1.15,True)
c.save()

# Root hierarchy.
root=create_schematic("pickleball_robot_simple"); root.set_paper_size("A4")
root.set_title_block(title="Pickleball Robot - Simple Hobby Controller",date="2026-07-12",rev="H1-SIMPLE",company="Harrison")
root.add_text("SIMPLE HOBBY CONTROLLER - TWO READABLE SCHEMATIC PAGES",(70,20),size=2.0,bold=True)
defs=[("Power + dual wheel driver","simple_01_power_motors.kicad_sch",(35,45)),("ESP32 + servos + UART","simple_02_esp_servos_uart.kicad_sch",(35,85))]
ids=[]
for name,file,pos in defs: ids.append(root.add_sheet(name,file,pos,(130,25),project_name="pickleball_robot_simple"))
root.add_text("Open a page from the hierarchy panel. Global labels join nets between the two pages.",(45,125),size=1.3)
root.save_as(OUT/"pickleball_robot_simple.kicad_sch",preserve_format=False)
root_raw=(OUT/"pickleball_robot_simple.kicad_sch").read_text(encoding="utf-8"); root_uuid=re.search(r'\(uuid "([0-9a-f-]+)"\)',root_raw).group(1)
for page,((name,file,pos),sid) in enumerate(zip(defs,ids),2):
    path=OUT/file; raw=path.read_text(encoding="utf-8"); cuid=re.search(r'\(uuid "([0-9a-f-]+)"\)',raw).group(1)
    raw=raw.replace(f'(project "{Path(file).stem}"','(project "pickleball_robot_simple"').replace(f'(path "/{cuid}"',f'(path "/{root_uuid}/{sid}"')
    raw=raw.replace('(sheet_instances\n\t\t(path "/"',f'(sheet_instances\n\t\t(path "/{root_uuid}/{sid}"').replace('(page "1")\n\t\t)\n\t)\n\t(embedded_fonts',f'(page "{page}")\n\t\t)\n\t)\n\t(embedded_fonts')
    path.write_text(raw,encoding="utf-8")
pro=OUT/"pickleball_robot_simple.kicad_pro"
pro.write_text(json.dumps({"board":{},"boards":[],"cvpcb":{},"erc":{},"libraries":{},"meta":{"filename":pro.name,"version":1},"net_settings":{},"pcbnew":{},"schematic":{},"text_variables":{}},indent=2),encoding="utf-8")
(OUT/"fp-lib-table").write_text('(fp_lib_table\n  (lib (name "PickleballRobot")(type "KiCad")(uri "${KIPRJMOD}/../PickleballRobot.pretty")(options "")(descr "Pickleball robot custom footprints"))\n)\n',encoding="utf-8")
print("Generated simple_hobby_controller/pickleball_robot_simple.kicad_pro")
