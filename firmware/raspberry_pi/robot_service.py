#!/usr/bin/env python3
"""PickleBot Raspberry Pi camera stream and ESP USB-serial bridge."""

from __future__ import annotations

import glob
import json
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import serial


class SerialBridge:
    def __init__(self) -> None:
        self.port: serial.Serial | None = None
        self.path = ""
        self.lock = threading.Lock()
        threading.Thread(target=self._connection_loop, daemon=True).start()

    @staticmethod
    def _find_port() -> str | None:
        candidates = glob.glob("/dev/serial/by-id/*")
        candidates += glob.glob("/dev/ttyUSB*")
        return candidates[0] if candidates else None

    def _connection_loop(self) -> None:
        while True:
            if self.port is None or not self.port.is_open:
                path = self._find_port()
                if path:
                    try:
                        port = serial.Serial(path, 115200, timeout=0.2, write_timeout=0.2)
                        port.dtr = False
                        port.rts = False
                        self.port = port
                        self.path = path
                        self.send("PING")
                    except serial.SerialException:
                        self.port = None
                        self.path = ""
            time.sleep(1)

    def send(self, command: str) -> bool:
        with self.lock:
            try:
                if self.port is None or not self.port.is_open:
                    return False
                self.port.write((command.strip() + "\n").encode("ascii"))
                self.port.flush()
                return True
            except (serial.SerialException, OSError):
                self.port = None
                self.path = ""
                return False


class Camera:
    def __init__(self) -> None:
        self.frame: bytes | None = None
        self.error = "not started"
        self.condition = threading.Condition()
        self.process: subprocess.Popen[bytes] | None = None
        self.started = False

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        command_name = shutil.which("rpicam-vid") or shutil.which("libcamera-vid")
        if not command_name:
            self.error = "rpicam-vid is not installed"
            return
        command = [
            command_name, "--timeout", "0", "--nopreview", "--codec", "mjpeg",
            "--width", "640", "--height", "480", "--framerate", "20",
            "--output", "-",
        ]
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.error = ""
            buffer = bytearray()
            assert self.process.stdout is not None
            while True:
                chunk = self.process.stdout.read(4096)
                if not chunk:
                    self.error = "camera process stopped"
                    return
                buffer.extend(chunk)
                while True:
                    start = buffer.find(b"\xff\xd8")
                    end = buffer.find(b"\xff\xd9", start + 2) if start >= 0 else -1
                    if start < 0 or end < 0:
                        if len(buffer) > 2_000_000:
                            del buffer[:-2]
                        break
                    frame = bytes(buffer[start:end + 2])
                    del buffer[:end + 2]
                    with self.condition:
                        self.frame = frame
                        self.condition.notify_all()
        except OSError as exc:
            self.error = str(exc)

    def wait_for_frame(self, previous: bytes | None) -> bytes | None:
        self.start()
        with self.condition:
            self.condition.wait_for(lambda: self.frame is not None and self.frame is not previous, timeout=2)
            return self.frame


SERIAL = SerialBridge()
CAMERA = Camera()


class Handler(BaseHTTPRequestHandler):
    server_version = "PickleBot/1"

    def _headers(self, status: int, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            previous = None
            try:
                while True:
                    frame = CAMERA.wait_for_frame(previous)
                    if frame is None:
                        continue
                    previous = frame
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                    self.wfile.write(frame + b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                return
        elif parsed.path == "/health":
            body = json.dumps({
                "ok": True,
                "serial": SERIAL.path or None,
                "camera_error": CAMERA.error or None,
            }).encode()
            self._headers(200, "application/json")
            self.wfile.write(body)
        elif parsed.path == "/api/drive":
            left = max(-100, min(100, int(query.get("l", ["0"])[0])))
            right = max(-100, min(100, int(query.get("r", ["0"])[0])))
            ok = SERIAL.send(f"DRIVE,{left},{right}")
            self._headers(200 if ok else 503, "application/json")
            self.wfile.write(json.dumps({"ok": ok}).encode())
        elif parsed.path == "/api/stop":
            ok = SERIAL.send("STOP")
            self._headers(200 if ok else 503, "application/json")
            self.wfile.write(json.dumps({"ok": ok}).encode())
        else:
            body = b"PickleBot Pi service. Use /stream or /health.\n"
            self._headers(200, "text/plain")
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("PickleBot service listening on http://0.0.0.0:8080")
    server.serve_forever()
