"""Fail-fast semantic checks that KiCad ERC cannot perform.

Run after generate_kicad_multisheet.py and before PCB updates.
"""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parent
src = (ROOT / "generate_kicad_multisheet.py").read_text(encoding="utf-8")

required = {
    "LM2596 catch diode K=SW/A=GND": 'p.two("D3","CTRL_SW","GND")',
    "Pi catch diode K=SW/A=GND": 'p.two("D9","PI_BUCK_SW","GND")',
    "6V catch diode K=SW/A=GND": 's.two("D10","SERVO_BUCK_SW","GND")',
    "8.4V catch diode K=SW/A=GND": 'h.two("D11","MAIN8_SW","GND")',
    "battery ADC low clamp": 'p.two("D2","GPIO33_BAT_ADC","GND")',
    "battery ADC high clamp": 'p.two("D14","3V3","GPIO33_BAT_ADC")',
    "left current ADC low clamp": 'm.two(dlo,cs_adc,"GND")',
    "left/right current ADC high clamp": 'm.two(dhi,"3V3",cs_adc)',
    "left fault OR polarity": 'c.two("D15","LEFT_DIAG","MOTOR_DIAG")',
    "right fault OR polarity": 'c.two("D16","RIGHT_DIAG","MOTOR_DIAG")',
    "status LED polarity": 'c.two(dd,"MOTOR_DIAG" if dd=="D8" else "GND",m)',
    "8.4 V LED polarity": 'h.two("D13","GND","LED_MAIN8")',
    "input TVS is bidirectional": 'p.part("Device:D_TVS","D1","SMBJ15CA"',
    "actuator TVS is bidirectional": 'p.part("Device:D_TVS","D21","SMBJ15CA ACT TVS"',
    "6 V TVS is bidirectional": 's.part("Device:D_TVS","D4","SMBJ8.0CA BIDIRECTIONAL"',
    "8.4 V TVS is bidirectional": 'h.part("Device:D_TVS","D12","SMBJ10CA BIDIRECTIONAL"',
    "Pi EN divider": '(3,"PI_EN_UVLO")',
    "XT60 library polarity": 'p.net("J1",1,"GND"); p.net("J1",2,"BAT_RAW")',
    "servo enable renamed accurately": 'SERVO_POWER_ENABLE',
    "motor JST power isolation": 'PH MOTOR POWER BYPASS - NORMALLY OPEN',
}
for name, needle in required.items():
    if needle not in src:
        raise SystemExit(f"FAIL: {name}")

for bad in [
    'p.two("D3","GND","CTRL_SW")',
    'p.two("D9","GND","PI_BUCK_SW")',
    's.two("D10","GND","SERVO_BUCK_SW")',
    'h.two("D11","GND","MAIN8_SW")',
    '(3,"VBAT_SW"),(4,"PI_RT")',
    'GPIO5_RIGHT_DIAG',
    'GPIO2_SERVO_OE',
    'SMBJ15A',
    'SMBJ8.0A',
    'SMBJ10A',
]:
    if bad in src:
        raise SystemExit(f"FAIL: forbidden legacy connection remains: {bad}")

# Feedback and UVLO nominal calculations.
rails = {
    "PI_5V": (54.9e3, 10.2e3, 5.106),
    "SERVO_6V": (66.3e3, 10.2e3, 6.000),
    "MAIN_8V4": (96.9e3, 10.2e3, 8.400),
}
for name, (top, bottom, target) in rails.items():
    actual = 0.8 * (1 + top / bottom)
    if not math.isclose(actual, target, abs_tol=0.025):
        raise SystemExit(f"FAIL: {name} computes to {actual:.3f} V")

# TPS54560B EN divider, using typical 1.2V threshold/1.2uA pin current
# and 3.4uA hysteresis current from the datasheet.
rtop, rbottom = 267e3, 34.0e3
start = 1.2 + rtop * (1.2 / rbottom - 1.2e-6)
stop = start - rtop * 3.4e-6
if not (10.0 <= start <= 10.5 and 9.1 <= stop <= 9.7):
    raise SystemExit(f"FAIL: Pi UVLO computes to start={start:.2f}, stop={stop:.2f}")

generated = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.glob("0?_*.kicad_sch"))
for ref in ["R43", "R44", "J20", "C30", "C40", "C61", "R36", "C68", "R113", "C69", "R114", "C70"]:
    marker = f'(property "Reference" "{ref}"'
    pos = generated.find(marker)
    if pos < 0 or "(dnp yes)" not in generated[max(0, pos-500):pos]:
        raise SystemExit(f"FAIL: {ref} is not a real KiCad DNP")

for ref in ["C18", "C19"]:
    marker = f'(property "Reference" "{ref}"'
    pos = generated.find(marker)
    if pos < 0 or "(on_board no)" not in generated[max(0, pos-500):pos]:
        raise SystemExit(f"FAIL: {ref} is not excluded from PCB")

print(f"PASS: semantic audit; rails OK; Pi UVLO start {start:.2f} V / stop {stop:.2f} V")
