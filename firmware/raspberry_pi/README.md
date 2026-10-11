# Raspberry Pi service

This service streams the Pi camera to the ESP webpage and provides an HTTP to
USB-serial bridge for the ESP32. It expects the ESP programming port to appear
as `/dev/ttyUSB*` or `/dev/serial/by-id/*` and sends commands at 115200 baud.

The camera stream is available at `http://PI_ADDRESS:8080/stream` and service
status at `http://PI_ADDRESS:8080/health`.

Installation and network configuration will be performed over SSH once the Pi
is powered and reachable. The service uses `rpicam-vid` from Raspberry Pi OS
and the Python dependency listed in `requirements.txt`.
