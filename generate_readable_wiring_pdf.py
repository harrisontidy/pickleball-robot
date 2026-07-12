"""Create the readable, multi-page companion PDF for the controller.

The KiCad schematic remains the PCB/netlist source.  This PDF is intentionally
laid out as a wiring book so it can be read on screen or printed without zooming.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "pickleball_robot_controller.html"
PDF = ROOT / "pickleball_robot_controller.pdf"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

css = r'''
@page { size: A4 landscape; margin: 12mm; }
* { box-sizing: border-box; }
body { margin:0; color:#14213d; font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; }
.page { page-break-after: always; min-height: 180mm; position:relative; }
.page:last-child { page-break-after: auto; }
h1 { color:#003d79; margin:0 0 3mm; font-size:25pt; }
h2 { color:#005b96; border-bottom:2px solid #39a9db; padding-bottom:2mm; margin:0 0 4mm; font-size:17pt; }
h3 { color:#005b96; margin:4mm 0 2mm; font-size:12pt; }
p { margin: 1.5mm 0; line-height:1.35; }
.sub { color:#4a5a70; font-size:11pt; }
.grid2 { display:grid; grid-template-columns: 1fr 1fr; gap:7mm; }
.grid3 { display:grid; grid-template-columns: 1fr 1fr 1fr; gap:5mm; }
.card { border:1px solid #a9cde5; border-radius:4px; padding:3.5mm; background:#f8fcff; }
.warn { border-left:5px solid #ed7d31; background:#fff4eb; padding:3mm 4mm; margin:3mm 0; }
.ok { border-left:5px solid #31a24c; background:#effaf1; padding:3mm 4mm; margin:3mm 0; }
table { width:100%; border-collapse:collapse; margin:2mm 0; font-size:9.2pt; }
th { background:#005b96; color:white; text-align:left; padding:2mm; }
td { border:1px solid #b9cbd8; padding:1.6mm 2mm; vertical-align:top; }
tr:nth-child(even) td { background:#f5faff; }
.diagram { width:100%; height:76mm; border:1px solid #a9cde5; border-radius:4px; background:#fbfdff; }
.foot { position:absolute; bottom:0; color:#526777; font-size:8.5pt; }
.tag { display:inline-block; font-weight:bold; border-radius:10px; padding:1mm 2.5mm; margin-right:2mm; color:white; font-size:8.5pt; }
.blue { background:#1677b9; } .green { background:#298c44; } .orange { background:#d46916; } .red { background:#bf3030; }
code { font-family: Consolas, monospace; background:#edf3f7; padding:0.5mm 1mm; }
ul { margin:1.5mm 0 1.5mm 5mm; padding-left:4mm; }
li { margin:1mm 0; }
'''

def box(x, y, w, h, title, lines, color="#1677b9"):
    items = "".join(f'<text x="{x+8}" y="{y+34+i*15}" class="line">{line}</text>' for i, line in enumerate(lines))
    return f'''<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#f8fcff" stroke="{color}" stroke-width="2"/>
<rect x="{x}" y="{y}" width="{w}" height="26" rx="8" fill="{color}"/><text x="{x+8}" y="{y+18}" class="head">{title}</text>{items}</g>'''

def arrow(x1, y1, x2, y2, label=""):
    midx, midy = (x1+x2)/2, (y1+y2)/2
    return f'<path d="M{x1},{y1} L{x2},{y2}" class="wire" marker-end="url(#arrow)"/><text x="{midx}" y="{midy-5}" class="wirelabel">{label}</text>'

svg_style = '''<style>.head{font:bold 14px Arial;fill:white}.line{font:12px Arial;fill:#14213d}.wire{stroke:#14213d;stroke-width:2;fill:none}.wirelabel{font:bold 11px Arial;fill:#005b96;text-anchor:middle}</style><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#14213d"/></marker></defs>'''

power_svg = f'''<svg class="diagram" viewBox="0 0 1080 300">{svg_style}
{box(28,112,150,85,'3S LiPo / XT60',['9–12.6 V battery','35 C = capability'])}
{box(230,112,165,85,'SAFETY INPUT',['F1 blade fuse','latching E-stop','VBAT_SW bus'],'#d46916')}
{box(460,20,175,85,'PI POWER — U4',['TPS54560B','5 V / 5 A','F3 → J9 Mini-Fit'],'#1677b9')}
{box(460,112,175,85,'CONTROL — U1',['LM2596S-5','5 V logic only','ESP32 + sensors'],'#298c44')}
{box(460,204,175,85,'SERVO — U10',['TPS54560B','6 V / 5 A','F2 → servo headers'],'#d46916')}
{box(720,20,155,85,'RASPBERRY PI 5',['Pi / Hailo rail','not motor power'],'#1677b9')}
{box(720,112,155,85,'ESP32 + LOGIC',['ESP32-PICO-KIT','PCA9685 / encoders'],'#298c44')}
{box(720,204,155,85,'ARM SERVOS',['25 kg main','MG996R elbow','MG90S wrist'],'#d46916')}
{box(925,112,135,85,'WHEEL DRIVE',['U2 / U3 VNH5019','J4 / J5 motors'],'#bf3030')}
{arrow(178,154,230,154,'battery')}{arrow(395,130,460,62,'VBAT_SW')}{arrow(395,154,460,154,'VBAT_SW')}{arrow(395,178,460,246,'VBAT_SW')}{arrow(395,154,925,154,'VBAT_SW')}
{arrow(635,62,720,62,'5 V')}{arrow(635,154,720,154,'5 V / 3.3 V')}{arrow(635,246,720,246,'6 V')}</svg>'''

motor_svg = f'''<svg class="diagram" viewBox="0 0 1080 300">{svg_style}
{box(28,80,190,140,'J4 LEFT MOTOR CABLE',['1 RED → motor OUT A','2 WHITE → motor OUT B','3 BLACK → GND','4 BLUE → 3.3 V encoder','5 YELLOW → encoder A','6 GREEN → encoder B'],'#bf3030')}
{box(330,80,190,140,'U2 VNH5019A-E',['H-bridge','PWM / INA / INB','fault + current sense','local 470 uF bulk'],'#bf3030')}
{box(630,80,190,140,'ESP32',['GPIO25: left PWM','GPIO26/27: direction','GPIO34/35: encoder','GPIO36: current sense'],'#298c44')}
{box(862,80,190,140,'J5 RIGHT MOTOR CABLE',['same six pin order','right driver = U3','GPIO14: PWM','GPIO4/13: direction'],'#bf3030')}
{arrow(218,150,330,150,'motor + encoder')}{arrow(520,150,630,150,'3.3 V logic')}{arrow(820,150,862,150,'mirror channel')}</svg>'''

servo_svg = f'''<svg class="diagram" viewBox="0 0 1080 300">{svg_style}
{box(28,105,175,90,'ESP32 I²C',['GPIO21 = SDA','GPIO22 = SCL','GPIO2 = output enable'],'#298c44')}
{box(286,105,185,90,'U5 PCA9685',['3.3 V logic','PWM channels 0–2','I²C servo controller'],'#1677b9')}
{box(550,20,190,90,'6 V POWER',['U10 → F2 → C40','TVS + 2200 uF','regulated servo rail'],'#d46916')}
{box(550,190,190,90,'SERVO HEADERS',['J12 main swing','J13 elbow','J14 wrist'],'#d46916')}
{box(840,105,190,90,'STANDARD RC PLUG',['pin 1 GND (black/brown)','pin 2 +6 V (red)','pin 3 PWM (yellow/orange)'],'#d46916')}
{arrow(203,150,286,150,'I²C')}{arrow(471,150,550,235,'PWM 0 / 1 / 2')}{arrow(645,110,645,190,'6 V')}{arrow(740,235,840,150,'3-pin 2.54 mm')}</svg>'''

pages = [
f'''<section class="page"><h1>Pickleball Robot Controller</h1><p class="sub">Readable wiring and build book · Rev R1 · companion to the KiCad PCB source</p><div class="ok"><b>Use this PDF to understand and wire the robot.</b> The KiCad schematic remains the authoritative PCB/netlist file; this version deliberately splits the system into readable pages.</div><h2>1. Power architecture</h2>{power_svg}<div class="grid3"><div class="card"><span class="tag blue">PI</span><b>5 V / 5 A</b><p>U4 powers only the Raspberry Pi 5 and Hailo connection. It is a supply capability, not constant draw.</p></div><div class="card"><span class="tag green">LOGIC</span><b>5 V control rail</b><p>U1 powers ESP32 carrier and low-current logic. Never use it for the Pi or servos.</p></div><div class="card"><span class="tag orange">SERVOS</span><b>6 V / 5 A</b><p>U10 supplies the three arm servos. Avoid deliberately stalling multiple servos at once.</p></div></div><p class="foot">Page 1 of 5 · Battery has one voltage; regulators make the separate rails.</p></section>''',
f'''<section class="page"><h2>2. Raspberry Pi, ESP32, and control wiring</h2><div class="grid2"><div><h3>Pi ↔ ESP32 UART: J10</h3><table><tr><th>J10 signal</th><th>Connects to</th><th>Purpose</th></tr><tr><td>Pi TX</td><td>ESP32 RX0 / GPIO3</td><td>Pi sends drive commands</td></tr><tr><td>ESP32 TX0 / GPIO1</td><td>Pi RX</td><td>ESP32 returns status</td></tr><tr><td>GND</td><td>Pi GND</td><td>Required shared reference</td></tr><tr><td>I²C SDA/SCL</td><td>GPIO21 / GPIO22</td><td>Optional expansion / servo controller</td></tr></table><div class="warn"><b>UART is 3.3 V only.</b> Do not connect a 5 V UART signal. Do not actively use Pi UART while the ESP32 USB serial adapter is driving RX0/TX0.</div></div><div><h3>ESP32 socket assignments</h3><table><tr><th>Function</th><th>ESP32 pin</th></tr><tr><td>Left PWM / direction</td><td>GPIO25 / GPIO26 / GPIO27</td></tr><tr><td>Right PWM / direction</td><td>GPIO14 / GPIO13 / GPIO4</td></tr><tr><td>Left / right encoder</td><td>GPIO34/35 and GPIO37/38</td></tr><tr><td>Battery ADC</td><td>GPIO33</td></tr><tr><td>Servo I²C</td><td>GPIO21 SDA / GPIO22 SCL</td></tr></table><h3>Board status LEDs</h3><p><span class="tag green">GREEN</span>logic 5 V &nbsp; <span class="tag blue">BLUE</span>Pi 5 V &nbsp; <span class="tag orange">AMBER</span>servo 6 V &nbsp; <span class="tag red">RED</span>motor fault</p></div></div><p class="foot">Page 2 of 5 · Pi handles vision; ESP32 handles immediate motor and servo control.</p></section>''',
f'''<section class="page"><h2>3. Wheel motors and encoders</h2>{motor_svg}<h3>Both six-pin motor connectors: J4 left and J5 right</h3><table><tr><th>Pin</th><th>Cable colour</th><th>Function</th><th>Important check</th></tr><tr><td>1</td><td>Red</td><td>Motor terminal A</td><td rowspan="2">If a wheel goes backwards, swap the two motor wires in software or at the connector.</td></tr><tr><td>2</td><td>White</td><td>Motor terminal B</td></tr><tr><td>3</td><td>Black</td><td>Encoder ground</td><td rowspan="4">Confirm this exact order against the plug before ordering the PCB.</td></tr><tr><td>4</td><td>Blue</td><td>Encoder +3.3 V</td></tr><tr><td>5</td><td>Yellow</td><td>Encoder channel A</td></tr><tr><td>6</td><td>Green</td><td>Encoder channel B</td></tr></table><div class="warn"><b>Connector:</b> 6-pin JST-PH, 2.00 mm pitch. The board footprint assumes the 10 mm pin-1-to-pin-6 measurement you made.</div><p class="foot">Page 3 of 5 · Normal prototype assumption: 3 A peak per wheel. The VNH5019 drivers provide margin.</p></section>''',
f'''<section class="page"><h2>4. Three-degree-of-freedom arm servos</h2>{servo_svg}<div class="grid2"><div class="card"><h3>What plugs where</h3><table><tr><th>Header</th><th>Servo</th><th>PCA9685 channel</th></tr><tr><td>J12</td><td>Main 25 kg swing servo</td><td>0</td></tr><tr><td>J13</td><td>MG996R elbow servo</td><td>1</td></tr><tr><td>J14</td><td>MG90S wrist servo</td><td>2</td></tr></table></div><div class="card"><h3>Safe first test</h3><ol><li>Power the board from a current-limited bench supply.</li><li>Check the amber LED and measure 6.0 V at a servo header.</li><li>Connect one servo only, with arm free to move.</li><li>Use slow movements and PWM limits before connecting all three.</li></ol></div></div><p class="foot">Page 4 of 5 · Servo headers are ordinary 2.54 mm male pins, not JST-XH.</p></section>''',
f'''<section class="page"><h2>5. Build and PCB-layout checklist</h2><div class="grid2"><div><h3>Easy normal-iron parts</h3><ul><li>All 0805 resistors and small ceramic capacitors</li><li>Through-hole 220 µF / 1000 µF / 2200 µF electrolytic capacitors</li><li>JST-PH motor headers, Pi connector, XT60 pigtail connector, servo headers</li><li>Fuses and large terminal parts</li></ul><h3>Heat gun / paste parts</h3><ul><li>U2/U3 VNH5019 motor drivers</li><li>U4/U10 TPS54560B buck regulators</li><li>U5 PCA9685 and large power inductors</li></ul><p>The exact manufacturer part numbers are in <code>ORDERING_GUIDE.md</code>.</p></div><div><h3>Do before ordering</h3><ol><li>Open the KiCad project and assign/verify every footprint.</li><li>Place the high-current parts first; use wide copper pours and thermal vias.</li><li>Keep buck switch nodes short and away from encoder/UART traces.</li><li>Keep ESP32 antenna area clear of copper and components.</li><li>Run ERC, then update PCB from schematic and run DRC.</li><li>Print J4/J5 at 1:1 scale and compare with your physical motor plug.</li></ol><div class="warn"><b>Do not power the Pi or servos from the ESP32 logic rail.</b> Each has its own regulator on the same 3S battery.</div></div></div><p class="foot">Page 5 of 5 · Readable companion PDF generated from the project wiring plan.</p></section>'''
]

html = f'<!doctype html><html><head><meta charset="utf-8"><title>Pickleball Robot Wiring Book</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'
HTML.write_text(html, encoding="utf-8")
subprocess.run([str(EDGE), "--headless", "--disable-gpu", f"--print-to-pdf={PDF}", HTML.as_uri()], check=True)
print(PDF)
