"""Shared helpers for the tests and the measurement: a local magic-wormhole
mailbox and courier processes whose JSON events are collected with times."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


def free_port(kind=socket.SOCK_STREAM) -> int:
    with socket.socket(socket.AF_INET, kind) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Proc:
    """A courier process whose stdout JSON lines are collected with arrival times."""

    def __init__(self, argv, cwd):
        self.started = time.monotonic()
        self.proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True)
        self.lines: list[str] = []
        self.events: list[tuple[float, dict]] = []
        self.stderr = ""
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            self.lines.append(line)
            try:
                self.events.append((time.monotonic(), json.loads(line)))
            except ValueError:
                pass

    def _read_err(self):
        self.stderr = self.proc.stderr.read()

    def names(self):
        return [e.get("event") for _, e in self.events]

    def find(self, name):
        for at, event in self.events:
            if event.get("event") == name:
                return at, event
        return None

    def wait_event(self, name, timeout=60):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = self.find(name)
            if found:
                return found[1]
            if self.proc.poll() is not None and not self.find(name):
                time.sleep(0.2)
                found = self.find(name)
                if found:
                    return found[1]
                raise AssertionError(f"exited {self.proc.returncode} before {name}: "
                                     f"{self.names()} {self.stderr[-2000:]}")
            time.sleep(0.05)
        raise AssertionError(f"no {name} within {timeout}s: {self.names()}")

    def wait(self, timeout=30):
        code = self.proc.wait(timeout)
        time.sleep(0.2)
        return code

    def close(self):
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(10)
        for stream in (self.proc.stdout, self.proc.stderr):
            try:
                stream.close()
            except (OSError, ValueError):
                pass


class Mailbox:
    """A local magic-wormhole mailbox server (the public one is never used)."""

    def __init__(self, workdir: Path):
        port = free_port()
        self.url = f"ws://127.0.0.1:{port}/v1"
        twist = Path(sys.executable).with_name("twist")
        self.proc = subprocess.Popen(
            [str(twist), "wormhole-mailbox", f"--port=tcp:{port}:interface=127.0.0.1",
             f"--channel-db={workdir / 'relay.sqlite'}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                socket.create_connection(("127.0.0.1", port), 0.2).close()
                return
            except OSError:
                time.sleep(0.1)
        self.close()
        raise RuntimeError("local mailbox did not start")

    def close(self):
        self.proc.terminate()
        self.proc.wait(10)
