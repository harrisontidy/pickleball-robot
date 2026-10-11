# Autonomous Pickleball Robot

An autonomous mobile robot designed to rally with a human player. The robot combines computer vision, custom electronics, motor control, and a multi-axis paddle mechanism to detect a pickleball, move into position, and return it across the court.

This project is being built from the ground up, including the mechanical system, custom PCB, embedded firmware, vision pipeline, and control software.

## The idea

Most pickleball machines launch balls from one fixed position. This robot is designed to behave more like another player:

- See and track the incoming pickleball with a camera
- Use YOLO-based object detection to locate the ball in real time
- Estimate the ball's movement and expected interception point
- Drive left, right, forward, or backward to line up with the shot
- Control the paddle angle and swing timing with multiple servos
- Return the ball and reset for the next shot

The long-term goal is a robot that can rally autonomously instead of only feeding balls.

## How it works

```text
Camera
   |
   v
Raspberry Pi + YOLO vision
   |
   |  Ball position and robot commands
   v
ESP32 real-time controller
   |
   +----> Drive motors
   +----> Camera positioning
   +----> Paddle tilt
   +----> Main swing mechanism
   `----> Wrist / paddle angle
```

The Raspberry Pi handles camera processing and high-level decisions. The ESP32 handles the time-sensitive hardware control, including the wheel motors, servo positions, swing sequences, and safety watchdog.

## Project highlights

- Custom-designed KiCad PCB for the robot's electronics
- ESP32 firmware written with ESP-IDF
- Raspberry Pi camera and command service
- Phone-based Wi-Fi controls for manual driving and mechanism testing
- Four independently controlled servo axes
- Differential-drive chassis control
- Automatic wheel shutdown if commands are lost
- Physical emergency-stop support
- YOLO-based ball detection and autonomous positioning under development

## Current status

This is an active prototype. The custom controller, drive system, servo controls, Wi-Fi interface, Raspberry Pi communication, and paddle sequences are implemented. The next major stage is integrating and tuning the YOLO vision pipeline for reliable ball tracking, interception, and autonomous returns.

## Technology

- **Computer vision:** YOLO, OpenCV, Raspberry Pi camera
- **High-level control:** Raspberry Pi and Python
- **Real-time control:** ESP32-PICO-D4 and ESP-IDF
- **Electronics:** Custom PCB designed in KiCad
- **Motion:** DC drive motors and multi-axis servo paddle mechanism
- **Interface:** Onboard Wi-Fi control page and USB serial communication

## Engineering challenges

The hardest parts of the project are detecting a small, fast-moving ball, predicting where it will arrive, moving the robot quickly enough to intercept it, and coordinating several joints into a repeatable return stroke. The design also has to handle vibration, impact loading, electrical noise, changing lighting, and safe testing around a fast-moving paddle.

## Safety

The robot contains high-current motors and a fast swing mechanism. Keep the emergency stop accessible, test new movements at reduced power, and stay clear of the paddle while the system is energized.
