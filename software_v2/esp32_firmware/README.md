# ESP32 firmware

This is the ESP-IDF workspace for the robot's ESP32-PICO-KIT V4.1 controller.

Initial configuration:

- ESP-IDF 5.3.1
- target: `esp32` (ESP32-PICO-D4)
- serial port: `COM6`
- flash method: UART
- monitor baud: 115200

## Recorded servo calibration

The calibrated target pulse widths are:

- J3 / GPIO25 / MS62 main swing: 1500 us
- J4 / GPIO26 / MG996: 1500 us
- J5 / GPIO27 / paddle MG996: 1110 us
- J9 / GPIO21 / camera MG90: 1300 us

The checked-in firmware is deliberately in safe-idle mode
(`SERVO_OUTPUTS_ENABLED` is `0`). It does not generate servo PWM at startup, so
power cycling the controller will not command the mechanisms to move. Set the
flag to `1` only when deliberately applying the recorded positions; the program
then waits five seconds before enabling all four outputs.
