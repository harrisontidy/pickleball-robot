# ESP32 phone drive firmware

This ESP-IDF firmware provides phone and Raspberry Pi control for the robot.
At startup it commands all four servo headers to 1500 us and continuously
holds them there. The wheels remain stopped until commands arrive.

## Use it

1. Power the controller and wheel drivers, and release the physical E-stop.
2. On the phone, join Wi-Fi network `PickleBot-Drive`.
3. Enter password `picklebot`.
4. If the phone reports that the network has no internet, choose to stay
   connected.
5. Open `http://192.168.4.1` in a browser.
6. Select a speed, then press and hold a direction button. Releasing it stops.

The page offers corrected forward/reverse motion, pivot steering, individual
servo controls, a small test swing, a conservative coordinated swing, and a
Raspberry Pi camera panel. A 900 ms command watchdog stops both wheels if Wi-Fi,
browser, or Raspberry Pi commands are lost. Servo PWM continues independently.

## Hardware and build

- ESP-IDF: 5.3.1
- Target: `esp32` (ESP32-PICO-D4)
- Serial port: `COM6`
- Monitor baud: 115200
- Left driver inputs: GPIO32 / GPIO33
- Right driver inputs: GPIO13 / GPIO14
- Wheel PWM: 5 kHz
- J3 / GPIO25: camera pan, starts and holds at 1500 us
- J4 / GPIO26: swing tilt, starts and holds at 1500 us
- J5 / GPIO27: main swing, starts and holds at 1500 us
- J9 / GPIO21: wrist / paddle axial tilt, starts and holds at 1500 us

J7 is the power-only USB-C connector, not a servo header.

## Raspberry Pi USB serial commands

Connect the ESP programming/USB-UART port to a Raspberry Pi USB-A port. The
serial link runs at 115200 baud and accepts newline-terminated commands:

```text
DRIVE,50,50
DRIVE,-40,40
STOP
SERVO,0,1500
SWING,SMALL
SWING,MAIN
SWING,CENTER
PING
```

Servo channel numbers are 0=J3, 1=J4, 2=J5, and 3=J9. Nominal center is
1500 us. Web and serial manual controls permit 500-2500 us, but each joint's
safe physical end stops still need to be measured. The coordinated swing uses
1200-1800 us on J4/J9 and 900-2100 us on J5.

The motor drivers are powered from the PCB `VIN` input through the fuse path.
USB power can run the ESP32 and Wi-Fi but cannot power the motor outputs.

Build and flash from an ESP-IDF terminal:

```powershell
idf.py -p COM6 build flash monitor
```

The right motor is physically mirrored, and the complete chassis polarity is
also inverted because the original phone controller's forward and reverse
directions were backwards on the assembled robot. Both corrections are noted
beside the definitions in `main/main.c`.
