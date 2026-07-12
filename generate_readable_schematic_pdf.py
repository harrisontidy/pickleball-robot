"""Render a human-readable multi-page schematic companion PDF.

This deliberately uses one subsystem per A4 landscape page.  The KiCad file is
still the PCB authority; this file is the readable schematic handout.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "pickleball_robot_controller.html"
PDF = ROOT / "pickleball_robot_controller.pdf"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

CSS = '''
@page { size:A4 landscape; margin:10mm; }
*{box-sizing:border-box} body{margin:0;font-family:Arial,sans-serif;color:#172a3a} .page{page-break-after:always;min-height:185mm;position:relative}.page:last-child{page-break-after:auto} h1{font-size:24pt;color:#003d79;margin:0 0 2mm} h2{font-size:17pt;color:#005b96;margin:0 0 3mm;border-bottom:2px solid #1d9bd1;padding-bottom:2mm}.sub{color:#526777;margin:0 0 3mm}.sheet{width:100%;height:133mm;border:1px solid #92b9d2;background:#fff}.note{font-size:10pt;line-height:1.35;margin:2mm 0}.foot{position:absolute;bottom:0;color:#607786;font-size:8.5pt}.legend{font-size:9pt;margin:2mm 0}.tag{display:inline-block;padding:1mm 2.5mm;border-radius:9px;color:#fff;font-weight:bold;margin-right:2mm}.pwr{background:#bf3030}.logic{background:#298c44}.sig{background:#1677b9}.warn{background:#fff2e8;border-left:4px solid #d46916;padding:2mm 3mm}.wire{stroke:#172a3a;stroke-width:2;fill:none}.net{font:bold 12px Arial;fill:#005b96}.txt{font:12px Arial;fill:#172a3a}.small{font:10px Arial;fill:#172a3a}.ref{font:bold 11px Arial;fill:#172a3a}.pin{font:10px Consolas,monospace;fill:#172a3a}.ic{fill:#fffdf4;stroke:#805f00;stroke-width:2}.part{fill:#f9fcff;stroke:#1677b9;stroke-width:1.6}.pwrbox{fill:#fff8f7;stroke:#bf3030;stroke-width:1.6}.gnd{font:bold 13px Arial;fill:#172a3a}.frame{fill:none;stroke:#c9ddea;stroke-width:1}.title{font:bold 15px Arial;fill:#003d79}.node{fill:#172a3a}.dash{stroke:#788b97;stroke-width:1.4;stroke-dasharray:5 4;fill:none}
'''

def svg(body):
    return f'<svg class="sheet" viewBox="0 0 1120 600" xmlns="http://www.w3.org/2000/svg">{body}</svg>'

def line(x1,y1,x2,y2,cls="wire"): return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>'
def text(x,y,s,cls="txt",anchor="start"): return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{s}</text>'
def dot(x,y): return f'<circle cx="{x}" cy="{y}" r="3.3" class="node"/>'
def resistor(x,y,label,h=False):
    if h: return f'<rect x="{x}" y="{y-8}" width="48" height="16" class="part"/>{text(x+24,y-12,label,"ref","middle")}'
    return f'<rect x="{x-8}" y="{y}" width="16" height="48" class="part"/>{text(x+12,y+24,label,"ref")}'
def cap(x,y,label,h=False):
    if h: return f'{line(x,y-14,x,y+14)}{line(x+10,y-14,x+10,y+14)}{text(x-3,y-20,label,"ref")}'
    return f'{line(x-14,y,x+14,y)}{line(x-14,y+10,x+14,y+10)}{text(x+18,y+9,label,"ref")}'
def ic(x,y,w,h,title,pins):
    p=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" class="ic"/>{text(x+w/2,y+22,title,"ref","middle")}'
    for side,py,name in pins:
        px=x if side=='L' else x+w
        ex=px-25 if side=='L' else px+25
        p+=line(px,py,ex,py)+text(ex-3 if side=='L' else ex+3,py+4,name,"pin","end" if side=='L' else 'start')
    return p

# Page 1: battery and distribution
p1='''<rect x="15" y="15" width="1090" height="570" class="frame"/>
<text x="35" y="45" class="title">BATTERY INPUT, PROTECTION, AND POWER DISTRIBUTION</text>
<rect x="55" y="220" width="100" height="80" class="pwrbox"/><text x="105" y="248" class="ref" text-anchor="middle">J1</text><text x="105" y="267" class="txt" text-anchor="middle">XT60 PIGTAIL</text><text x="105" y="284" class="small" text-anchor="middle">3S LiPo</text>
<line x1="155" y1="240" x2="205" y2="240" class="wire"/><rect x="205" y="224" width="55" height="32" class="part"/><text x="232" y="219" class="ref" text-anchor="middle">F1</text><text x="232" y="274" class="small" text-anchor="middle">15 A blade</text>
<line x1="260" y1="240" x2="320" y2="240" class="wire"/><rect x="320" y="216" width="90" height="48" class="pwrbox"/><text x="365" y="237" class="ref" text-anchor="middle">E-STOP</text><text x="365" y="254" class="small" text-anchor="middle">external latch</text>
<line x1="410" y1="240" x2="960" y2="240" class="wire"/><text x="480" y="228" class="net">VBAT_SW (9–12.6 V)</text>
<line x1="105" y1="300" x2="105" y2="390" class="wire"/><line x1="105" y1="390" x2="960" y2="390" class="wire"/><text x="450" y="414" class="gnd">GND / BATTERY RETURN</text>
<line x1="500" y1="240" x2="500" y2="130" class="wire"/><circle cx="500" cy="240" r="3.3" class="node"/><rect x="430" y="60" width="140" height="70" class="ic"/><text x="500" y="86" class="ref" text-anchor="middle">U4 — PI BUCK</text><text x="500" y="106" class="txt" text-anchor="middle">TPS54560B · 5 V / 5 A</text><line x1="500" y1="130" x2="500" y2="150" class="wire"/><text x="507" y="148" class="pin">VIN</text><line x1="500" y1="130" x2="500" y2="150" class="wire"/><line x1="500" y1="60" x2="500" y2="45" class="wire"/><text x="508" y="49" class="net">PI_5V → F3 → J9</text>
<line x1="710" y1="240" x2="710" y2="130" class="wire"/><circle cx="710" cy="240" r="3.3" class="node"/><rect x="640" y="60" width="140" height="70" class="ic"/><text x="710" y="86" class="ref" text-anchor="middle">U1 — LOGIC BUCK</text><text x="710" y="106" class="txt" text-anchor="middle">LM2596S · +5V_CTRL</text><line x1="710" y1="60" x2="710" y2="45" class="wire"/><text x="718" y="49" class="net">ESP32 + LOGIC</text>
<line x1="900" y1="240" x2="900" y2="130" class="wire"/><circle cx="900" cy="240" r="3.3" class="node"/><rect x="830" y="60" width="140" height="70" class="ic"/><text x="900" y="86" class="ref" text-anchor="middle">U10 — SERVO BUCK</text><text x="900" y="106" class="txt" text-anchor="middle">TPS54560B · 6 V / 5 A</text><line x1="900" y1="60" x2="900" y2="45" class="wire"/><text x="908" y="49" class="net">SERVO_6V → F2</text>
<line x1="285" y1="240" x2="285" y2="330" class="wire"/><line x1="285" y1="330" x2="315" y2="330" class="wire"/><line x1="315" y1="330" x2="315" y2="390" class="wire"/><text x="318" y="330" class="ref">D1 SMBJ18A TVS</text>
<line x1="380" y1="240" x2="380" y2="330" class="wire"/><line x1="380" y1="330" x2="410" y2="330" class="wire"/><line x1="410" y1="330" x2="410" y2="390" class="wire"/><text x="414" y="330" class="ref">C1 1000 µF / 25 V</text>
<line x1="1030" y1="240" x2="1030" y2="390" class="wire"/><text x="1038" y="308" class="net">to U2/U3 motor drivers</text>'''

# Page 2: Pi buck detailed
p2='''<rect x="15" y="15" width="1090" height="570" class="frame"/><text x="35" y="45" class="title">U4 — RASPBERRY PI 5 V / 5 A BUCK REGULATOR</text>
<text x="35" y="72" class="net">VBAT_SW</text><line x1="95" y1="68" x2="230" y2="68" class="wire"/><line x1="145" y1="68" x2="145" y2="142" class="wire"/><text x="150" y="120" class="ref">C32–C35</text><text x="150" y="136" class="small">4 × 2.2 µF / 25 V / 0805</text><line x1="145" y1="142" x2="145" y2="500" class="wire"/><text x="130" y="520" class="gnd">GND</text>
<rect x="270" y="145" width="180" height="200" class="ic"/><text x="360" y="178" class="ref" text-anchor="middle">U4 TPS54560BDDA</text><text x="360" y="198" class="txt" text-anchor="middle">5 V / 5 A buck</text>
<line x1="230" y1="68" x2="230" y2="190" class="wire"/><line x1="230" y1="190" x2="270" y2="190" class="wire"/><text x="265" y="185" class="pin" text-anchor="end">VIN + EN</text>
<line x1="450" y1="240" x2="540" y2="240" class="wire"/><text x="458" y="232" class="pin">SW</text><rect x="540" y="220" width="55" height="40" class="part"/><text x="567" y="215" class="ref" text-anchor="middle">L2</text><text x="567" y="279" class="small" text-anchor="middle">6.8 µH</text><line x1="595" y1="240" x2="800" y2="240" class="wire"/><text x="670" y="228" class="net">PI_5V_RAW</text>
<line x1="510" y1="240" x2="510" y2="340" class="wire"/><text x="516" y="300" class="ref">D9 B560C</text><line x1="510" y1="340" x2="510" y2="500" class="wire"/>
<line x1="680" y1="240" x2="680" y2="360" class="wire"/><text x="688" y="300" class="ref">C38 + C39</text><text x="688" y="316" class="small">2 × 220 µF / 10 V low ESR</text><line x1="680" y1="360" x2="680" y2="500" class="wire"/>
<rect x="820" y="218" width="70" height="44" class="part"/><text x="855" y="212" class="ref" text-anchor="middle">F3 5 A</text><line x1="800" y1="240" x2="820" y2="240" class="wire"/><line x1="890" y1="240" x2="1000" y2="240" class="wire"/><text x="935" y="228" class="net" text-anchor="middle">PI_5V</text><rect x="1000" y="190" width="75" height="100" class="pwrbox"/><text x="1037" y="220" class="ref" text-anchor="middle">J9</text><text x="1037" y="240" class="txt" text-anchor="middle">Pi power</text><text x="1037" y="259" class="small" text-anchor="middle">2×5 V, 2×GND</text>
<line x1="360" y1="345" x2="360" y2="500" class="wire"/><text x="370" y="370" class="pin">GND + thermal pad</text><line x1="95" y1="500" x2="1000" y2="500" class="wire"/><text x="35" y="558" class="small">Feedback/compensation: R30 243 kΩ, R31 442 kΩ, R32 90.9 kΩ, R33 10.2 kΩ, C31 100 nF, C36 4.7 nF, C37 47 pF. Keep these close to U4 and away from SW.</text>'''

# Page 3 control and Pi signals
p3='''<rect x="15" y="15" width="1090" height="570" class="frame"/><text x="35" y="45" class="title">ESP32, RASPBERRY PI UART, ENCODERS, AND LOGIC POWER</text>
<rect x="55" y="105" width="225" height="310" class="ic"/><text x="167" y="132" class="ref" text-anchor="middle">J2 — ESP32-PICO-KIT V4.1 SOCKET</text><text x="75" y="170" class="pin">GPIO21  I²C SDA</text><text x="75" y="195" class="pin">GPIO22  I²C SCL</text><text x="75" y="220" class="pin">GPIO25/26/27  LEFT DRIVE</text><text x="75" y="245" class="pin">GPIO14/13/4  RIGHT DRIVE</text><text x="75" y="270" class="pin">GPIO34/35  LEFT ENCODER</text><text x="75" y="295" class="pin">GPIO37/38  RIGHT ENCODER</text><text x="75" y="320" class="pin">GPIO1 TX0 / GPIO3 RX0</text><text x="75" y="345" class="pin">GPIO33 BATTERY ADC</text><text x="75" y="385" class="pin">+5V_CTRL / GND / 3V3</text>
<line x1="280" y1="175" x2="470" y2="175" class="wire"/><text x="375" y="163" class="net" text-anchor="middle">I²C SDA / SCL</text><rect x="470" y="120" width="170" height="110" class="ic"/><text x="555" y="150" class="ref" text-anchor="middle">U5 PCA9685</text><text x="555" y="170" class="txt" text-anchor="middle">servo PWM expander</text><text x="555" y="195" class="small" text-anchor="middle">PWM0 / PWM1 / PWM2</text>
<line x1="280" y1="320" x2="470" y2="320" class="wire"/><text x="375" y="308" class="net" text-anchor="middle">3.3 V UART</text><rect x="470" y="270" width="170" height="100" class="part"/><text x="555" y="300" class="ref" text-anchor="middle">J10 — PI UART / CONTROL</text><text x="555" y="322" class="small" text-anchor="middle">TX ↔ RX through R40/R41 1 kΩ</text><text x="555" y="344" class="small" text-anchor="middle">GND, enable, fault, I²C</text>
<line x1="640" y1="320" x2="850" y2="320" class="wire"/><rect x="850" y="270" width="185" height="100" class="pwrbox"/><text x="942" y="300" class="ref" text-anchor="middle">RASPBERRY PI 5</text><text x="942" y="322" class="txt" text-anchor="middle">GPIO14 TX → ESP RX0</text><text x="942" y="344" class="txt" text-anchor="middle">GPIO15 RX ← ESP TX0</text>
<line x1="280" y1="270" x2="380" y2="270" class="wire"/><line x1="380" y1="270" x2="380" y2="470" class="dash"/><rect x="680" y="425" width="300" height="95" class="part"/><text x="830" y="452" class="ref" text-anchor="middle">ENCODER CONDITIONING</text><text x="830" y="475" class="txt" text-anchor="middle">U6–U9 74LVC1G14 Schmitt buffers</text><text x="830" y="495" class="small" text-anchor="middle">10 kΩ pull-up + 1 nF filter on each A/B signal</text><line x1="380" y1="470" x2="680" y2="470" class="dash"/>
<text x="55" y="555" class="small">Status LEDs: D5 green = +5V_CTRL; D6 blue = PI_5V; D7 amber = SERVO_6V; D8 red = motor fault.</text>'''

# Page 4 motors
p4='''<rect x="15" y="15" width="1090" height="570" class="frame"/><text x="35" y="45" class="title">LEFT AND RIGHT WHEEL-MOTOR CHANNELS</text>
<text x="45" y="80" class="title">LEFT CHANNEL</text><rect x="55" y="120" width="150" height="230" class="pwrbox"/><text x="130" y="150" class="ref" text-anchor="middle">J4 — LEFT CABLE</text><text x="75" y="185" class="pin">1 RED: motor A</text><text x="75" y="210" class="pin">2 WHITE: motor B</text><text x="75" y="235" class="pin">3 BLACK: GND</text><text x="75" y="260" class="pin">4 BLUE: encoder 3V3</text><text x="75" y="285" class="pin">5 YELLOW: encoder A</text><text x="75" y="310" class="pin">6 GREEN: encoder B</text>
<line x1="205" y1="195" x2="325" y2="195" class="wire"/><line x1="205" y1="220" x2="325" y2="220" class="wire"/><rect x="325" y="125" width="185" height="190" class="ic"/><text x="417" y="155" class="ref" text-anchor="middle">U2 VNH5019A-E</text><text x="417" y="180" class="txt" text-anchor="middle">left H-bridge</text><text x="345" y="215" class="pin">OUT A / OUT B</text><text x="345" y="245" class="pin">PWM / INA / INB</text><text x="345" y="270" class="pin">FAULT / current sense</text><line x1="417" y1="125" x2="417" y2="85" class="wire"/><text x="425" y="95" class="net">VBAT_SW</text><line x1="417" y1="315" x2="417" y2="390" class="wire"/><text x="425" y="370" class="gnd">GND</text><line x1="510" y1="250" x2="610" y2="250" class="wire"/><text x="555" y="238" class="net" text-anchor="middle">ESP32 GPIOs</text>
<text x="640" y="80" class="title">RIGHT CHANNEL</text><rect x="650" y="120" width="150" height="230" class="pwrbox"/><text x="725" y="150" class="ref" text-anchor="middle">J5 — RIGHT CABLE</text><text x="670" y="185" class="pin">same six-pin order</text><text x="670" y="210" class="pin">motor + encoder together</text><text x="670" y="235" class="pin">PH 2.00 mm plug</text><line x1="800" y1="195" x2="920" y2="195" class="wire"/><line x1="800" y1="220" x2="920" y2="220" class="wire"/><rect x="920" y="125" width="145" height="190" class="ic"/><text x="992" y="155" class="ref" text-anchor="middle">U3 VNH5019A-E</text><text x="992" y="180" class="txt" text-anchor="middle">right H-bridge</text><text x="940" y="215" class="pin">OUT A / OUT B</text><text x="940" y="245" class="pin">PWM / INA / INB</text><text x="940" y="270" class="pin">FAULT / current sense</text><line x1="992" y1="125" x2="992" y2="85" class="wire"/><text x="1000" y="95" class="net">VBAT_SW</text><line x1="992" y1="315" x2="992" y2="390" class="wire"/><text x="1000" y="370" class="gnd">GND</text>
<text x="45" y="455" class="small">Each driver: local 470 µF / 25 V bulk capacitor, 100 kΩ control pull-downs, 10 kΩ fault pull-up, 1 kΩ current-sense load, 10 nF current filter.</text><text x="45" y="490" class="small">Motor power is routed on pins 1–2; encoder power/signals are pins 3–6 and are conditioned before the ESP32.</text>'''

# Page 5 servos
p5='''<rect x="15" y="15" width="1090" height="570" class="frame"/><text x="35" y="45" class="title">THREE-DEGREE-OF-FREEDOM SERVO SUBSYSTEM</text>
<rect x="70" y="115" width="180" height="125" class="ic"/><text x="160" y="145" class="ref" text-anchor="middle">U10 TPS54560B</text><text x="160" y="167" class="txt" text-anchor="middle">regulated 6 V / 5 A</text><text x="160" y="190" class="small" text-anchor="middle">C46/C47 input · L3 · D10</text><text x="160" y="210" class="small" text-anchor="middle">C50 220 µF output</text><line x1="160" y1="240" x2="160" y2="320" class="wire"/><text x="168" y="280" class="net">SERVO_6V</text><rect x="125" y="320" width="70" height="40" class="part"/><text x="160" y="313" class="ref" text-anchor="middle">F2 7.5 A</text><line x1="160" y1="360" x2="160" y2="430" class="wire"/><line x1="160" y1="430" x2="925" y2="430" class="wire"/>
<rect x="360" y="115" width="190" height="155" class="ic"/><text x="455" y="145" class="ref" text-anchor="middle">U5 PCA9685PW</text><text x="455" y="168" class="txt" text-anchor="middle">16-channel PWM controller</text><text x="380" y="202" class="pin">SDA ← ESP32 GPIO21</text><text x="380" y="224" class="pin">SCL ← ESP32 GPIO22</text><text x="380" y="246" class="pin">PWM0 / PWM1 / PWM2</text><line x1="550" y1="240" x2="650" y2="240" class="wire"/><text x="600" y="228" class="net" text-anchor="middle">PWM signals</text>
<rect x="680" y="120" width="110" height="100" class="part"/><text x="735" y="150" class="ref" text-anchor="middle">J12</text><text x="735" y="172" class="txt" text-anchor="middle">MAIN SWING</text><text x="735" y="193" class="small" text-anchor="middle">25 kg servo</text><line x1="735" y1="220" x2="735" y2="430" class="wire"/><line x1="650" y1="240" x2="680" y2="240" class="wire"/>
<rect x="835" y="120" width="110" height="100" class="part"/><text x="890" y="150" class="ref" text-anchor="middle">J13</text><text x="890" y="172" class="txt" text-anchor="middle">ELBOW</text><text x="890" y="193" class="small" text-anchor="middle">MG996R</text><line x1="890" y1="220" x2="890" y2="430" class="wire"/><line x1="650" y1="255" x2="835" y2="255" class="wire"/>
<rect x="990" y="120" width="90" height="100" class="part"/><text x="1035" y="150" class="ref" text-anchor="middle">J14</text><text x="1035" y="172" class="txt" text-anchor="middle">WRIST</text><text x="1035" y="193" class="small" text-anchor="middle">MG90S</text><line x1="1035" y1="220" x2="1035" y2="430" class="wire"/><line x1="650" y1="270" x2="990" y2="270" class="wire"/>
<text x="360" y="500" class="ref">ALL THREE SERVO HEADERS: pin 1 = GND (black/brown), pin 2 = +6 V (red), pin 3 = PWM (yellow/orange/white)</text><text x="360" y="525" class="small">Headers are unshrouded 2.54 mm male servo pins. D4 TVS + C40 2200 µF sit on the servo rail at the distribution point.</text>'''

pages=[
('1. Battery and power distribution',p1,'This page shows the complete high-current distribution from the 3S battery.'),
('2. Raspberry Pi power regulator',p2,'All U4 parts are shown on this page; keep its switch loop compact on the PCB.'),
('3. ESP32 and Pi signals',p3,'Visible signal wiring and pin roles; GPIO names match the KiCad PCB source.'),
('4. Wheel motors and encoders',p4,'Each physical motor uses one six-pin JST-PH connector.'),
('5. Arm servos',p5,'The arm has its own regulated 6 V rail and standard 2.54 mm servo headers.')]

out=[]
for i,(title,diagram,note) in enumerate(pages,1):
    out.append(f'<section class="page"><h1>Pickleball Robot — {title}</h1><p class="sub">Readable schematic companion · all lines are electrical connections; named nets are blue.</p>{svg(diagram)}<p class="note">{note}</p><p class="foot">Sheet {i} of {len(pages)} · PCB source: pickleball_robot_controller.kicad_sch</p></section>')

HTML.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(out)}</body></html>',encoding='utf-8')
subprocess.run([str(EDGE),'--headless','--disable-gpu',f'--print-to-pdf={PDF}',HTML.as_uri()],check=True)
print(PDF)
