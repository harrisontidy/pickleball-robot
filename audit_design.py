"""Fail-fast semantic checks that KiCad ERC cannot perform.

Run after generate_kicad_multisheet.py and before PCB updates.
"""
from pathlib import Path
import math
import re
from collections import Counter

ROOT = Path(__file__).resolve().parent
src = (ROOT / "generate_kicad_multisheet.py").read_text(encoding="utf-8")

required = {
    "LM2596 catch diode K=SW/A=GND": 'p.two("D3","CTRL_SW","GND")',
    "Pi catch diode K=SW/A=GND": 'p.two("D9","PI_BUCK_SW","GND")',
    "6V catch diode K=SW/A=GND": 's.two("D10","SERVO_BUCK_SW","GND")',
    "8.4V catch diode K=SW/A=GND": 'h.two("D11","MAIN8_SW","GND")',
    "battery ADC low clamp": 'b.two("D2","GPIO33_BAT_ADC","GND")',
    "battery ADC high clamp": 'b.two("D14","3V3","GPIO33_BAT_ADC")',
    "left current ADC low clamp": 'm.two(dlo,cs_adc,"GND")',
    "left/right current ADC high clamp": 'm.two(dhi,"3V3",cs_adc)',
    "left fault OR polarity": 'c.two("D15","LEFT_DIAG","MOTOR_DIAG")',
    "right fault OR polarity": 'c.two("D16","RIGHT_DIAG","MOTOR_DIAG")',
    "status LED polarity": 'c.two(dd,"MOTOR_DIAG" if dd=="D8" else "GND",m)',
    "8.4 V LED polarity": 'h.two("D13","GND","LED_MAIN8")',
    "input TVS is bidirectional": 'b.part("Device:D_TVS","D1","SMBJ15CA"',
    "actuator TVS is bidirectional": 'b.part("Device:D_TVS","D21","SMBJ15CA ACT TVS"',
    "6 V TVS is bidirectional": 's.part("Device:D_TVS","D4","SMBJ8.0CA BIDIRECTIONAL"',
    "8.4 V TVS is bidirectional": 'h.part("Device:D_TVS","D12","SMBJ10CA BIDIRECTIONAL"',
    "Pi EN divider": '(3,"PI_EN_UVLO")',
    "XT60 library polarity": 'b.net("J1",1,"GND"); b.net("J1",2,"BAT_RAW")',
    "servo enable renamed accurately": 'SERVO_POWER_ENABLE',
    "motor JST power isolation": 'PH MOTOR POWER BYPASS - NORMALLY OPEN',
    "whole-board LVD controller": 'Power_Management:LTC4365TS8',
    "fuse precedes disconnect": 'b.two("F1","BAT_RAW","BAT_FUSED")',
    "back-to-back LVD sources": 'LVD_COMMON_SOURCE',
    "input LVD FET orientation": 'b.net("Q5",1,"LVD_GATE_Q5"); b.net("Q5",2,"BAT_FUSED"); b.net("Q5",3,"LVD_COMMON_SOURCE")',
    "output LVD FET orientation": 'b.net("Q6",1,"LVD_GATE_Q6"); b.net("Q6",2,"VBAT_SW"); b.net("Q6",3,"LVD_COMMON_SOURCE")',
    "LVD monitors protected output": '(7,"VBAT_SW")',
    "LVD divider top": 'b.two("R115","BAT_FUSED","LVD_UV")',
    "LVD divider middle": 'b.two("R116","LVD_UV","LVD_OV")',
    "LVD divider bottom": 'b.two("R117","LVD_OV","GND")',
    "three guaranteed servo buffers": 'SN74AHCT1G125DBVR 3V3-TO-4V85 PWM',
    "servo buffers lose power with servo rails": '(5,"WRIST_4V85")',
    "servo buffers disabled with PCA": '(1,"GPIO32_SERVO_OE")',
    "MG90S dedicated rail": 'servo(2,"J14","WRIST MG90S",375,"WRIST_4V85")',
    "MG90S LDO enable": '(1,"SERVO_POWER_ENABLE"),(2,"SERVO_6V"),(3,"GND"),(4,"WRIST_4V85_RAW"),(5,"WRIST_LDO_ADJ")',
    "fail-safe E-stop coil connector": 'b.net("J21",1,"VBAT_SW"); b.net("J21",2,"GND")',
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

# LTC4365 stacked divider: BAT_FUSED -> R115 -> UV -> R116 -> OV -> R117 -> GND.
# Comparator falling thresholds are 0.500 V; UV reconnect is 0.525 V.
r_top, r_mid, r_bottom = 5.49e6, 90.9e3, 210e3
divider_total = r_top + r_mid + r_bottom
lvd_cutoff = 0.500 * divider_total / (r_mid + r_bottom)
lvd_reconnect = 0.525 * divider_total / (r_mid + r_bottom)
lvd_ov = 0.500 * divider_total / r_bottom
if not (9.4 <= lvd_cutoff <= 9.8 and 9.9 <= lvd_reconnect <= 10.3 and 13.5 <= lvd_ov <= 14.1):
    raise SystemExit(f"FAIL: LVD window computes to {lvd_cutoff:.2f}/{lvd_reconnect:.2f}/{lvd_ov:.2f} V")

wrist_rail = 1.21 * (1 + 3.01e3 / 1.00e3)
if not math.isclose(wrist_rail, 4.85, abs_tol=0.04):
    raise SystemExit(f"FAIL: MG90S rail computes to {wrist_rail:.3f} V")

if src.count('SN74AHCT1G125DBVR 3V3-TO-4V85 PWM') != 1:
    # The generator creates all three from one loop body; seeing the literal
    # exactly once guards the intended implementation rather than generated UUIDs.
    raise SystemExit("FAIL: servo PWM buffer generator is missing or duplicated")

generated = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.glob("0?_*.kicad_sch"))
numbered_refs = re.findall(r'\(property "Reference" "([A-Z#]+[0-9]+)"', generated)
duplicates = sorted(ref for ref, count in Counter(numbered_refs).items() if count > 1)
if duplicates:
    raise SystemExit(f"FAIL: duplicate schematic references: {', '.join(duplicates)}")
if generated.count('(property "Value" "SN74AHCT1G125DBVR 3V3-TO-4V85 PWM"') != 3:
    raise SystemExit("FAIL: generated schematic does not contain exactly three servo PWM buffers")
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

print(f"PASS: semantic audit; rails OK; Pi UVLO {start:.2f}/{stop:.2f} V; "
      f"whole-board LVD {lvd_cutoff:.2f} V off/{lvd_reconnect:.2f} V on, OV {lvd_ov:.2f} V; "
      f"MG90S rail {wrist_rail:.2f} V")
