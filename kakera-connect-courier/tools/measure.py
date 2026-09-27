#!/usr/bin/env python3
"""Measure what people carry, today and with the courier, using the real connector.

For each run it records
  - the long codes kakera-connect wrote (invite / answer), which people carry today,
  - the short code(s) the courier asks people to carry instead,
  - the time from starting the joiner's courier (the moment the short code is
    typed) until every side reports "connected".

All runs are kakera-connect's loopback-only mode with a local mailbox: the time
covers the courier, the mailbox round trips and a loopback ICE/DTLS setup, not
an Internet path or the people.

It also estimates a WAN-sized invite. The loopback SDP has one host candidate
(emitted for two components). The internet-connect report of daybreak-kakera
gathered 4 host and 2 server-reflexive candidates. The estimate adds such lines
to a real decoded invite and recompresses it the way the connector does
(zlib, best compression, base64url). It is an estimate, not a WAN observation.

usage: KAKERA_CONNECT=... python tools/measure.py [--pair-runs 5] [--room-runs 3]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import statistics
import sys
import tempfile
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from harness import Mailbox, Proc, free_port  # noqa: E402

COURIER = HERE / "courier.py"


def udp_port() -> int:
    return free_port(socket.SOCK_DGRAM)


def start(connector, relay, workdir, role, signal, *extra) -> Proc:
    argv = [sys.executable, str(COURIER), role, "--connector", connector,
            "--signal-dir", str(workdir / signal), "--game-port", str(udp_port()),
            "--stun-url", "none", "--timeout-secs", "60", "--relay", relay, *extra]
    return Proc(argv, workdir)


def short_codes(path: Path) -> dict[int, str]:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not path.exists():
        time.sleep(0.02)
    return {int(s): c for s, c in (line.split("\t") for line in path.read_text().splitlines())}


def finish(workdir: Path, signals, procs) -> None:
    for signal in signals:
        (workdir / signal / "stop.txt").touch()
    for p in procs:
        code = p.wait()
        p.close()
        if code != 0:
            raise RuntimeError(f"courier exited {code}: {p.stderr[-1000:]}")


def pair_run(connector, relay, workdir: Path) -> dict:
    host = start(connector, relay, workdir, "host", "h")
    code = short_codes(workdir / "h" / "short-code.txt")[1]
    typed = time.monotonic()
    join = start(connector, relay, workdir, "join", "j", "--code", code)
    host.wait_event("connected")
    join.wait_event("connected")
    connected = max(host.find("connected")[0], join.find("connected")[0])
    verified = join.find("courier_peer_verified")[0]
    finish(workdir, ["h", "j"], [host, join])
    return {
        "short_code_chars": len(code),
        "invite_chars": len((workdir / "h" / "invite.txt").read_text().strip()),
        "answer_chars": len((workdir / "j" / "answer.txt").read_text().strip()),
        "typed_to_verified_s": round(verified - typed, 3),
        "typed_to_connected_s": round(connected - typed, 3),
    }


def room_run(connector, relay, workdir: Path) -> dict:
    host = start(connector, relay, workdir, "host", "r0", "--participants", "4")
    codes = short_codes(workdir / "r0" / "short-code.txt")
    typed = time.monotonic()
    joins = [start(connector, relay, workdir, "join", f"r{s}", "--code", codes[s]) for s in (1, 2, 3)]
    for p in [host, *joins]:
        p.wait_event("connected", 90)
    connected = max(p.find("connected")[0] for p in [host, *joins])
    finish(workdir, ["r0", "r1", "r2", "r3"], [host, *joins])
    invites = [len((workdir / "r0" / f"invite-{s}.txt").read_text().strip()) for s in (1, 2, 3)]
    answers = [len((workdir / f"r{s}" / "answer.txt").read_text().strip()) for s in (1, 2, 3)]
    return {
        "short_code_chars": [len(codes[s]) for s in (1, 2, 3)],
        "invite_chars": invites,
        "answer_chars": answers,
        "typed_to_connected_s": round(connected - typed, 3),
    }


def wan_estimate(invite_path: Path) -> dict:
    code = invite_path.read_text().strip()
    prefix, body = code.split(".", 1)
    obj = json.loads(zlib.decompress(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))))
    lines = obj["sdp"].split("\r\n")
    last = max(i for i, line in enumerate(lines) if line.startswith("a=candidate"))
    # Shapes follow the real host line; addresses are documentation/private ranges.
    hosts = ["192.168.1.23", "172.29.160.1", "10.0.75.1", "192.168.56.1"]
    extra = []
    for n, ip in enumerate(hosts[1:], start=1):
        for comp in (1, 2):
            extra.append(f"a=candidate:{2693830880 + n} {comp} udp 2130706431 {ip} {50000 + n} typ host")
    for n, port in enumerate((61001, 61002), start=10):
        for comp in (1, 2):
            extra.append(f"a=candidate:{3000000000 + n} {comp} udp 1694498815 203.0.113.7 {port} "
                         f"typ srflx raddr 0.0.0.0 rport {50000 + n}")
    # Replace the loopback host address with the first private one.
    lines = [line.replace("127.0.0.1", hosts[0]) for line in lines]
    lines[last + 1:last + 1] = extra
    obj["sdp"] = "\r\n".join(lines)
    raw = json.dumps(obj, separators=(",", ":")).encode()
    wan = prefix + "." + base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip("=")
    return {"loopback_invite_chars": len(code), "estimated_wan_invite_chars": len(wan),
            "candidate_lines": sum(1 for line in lines if line.startswith("a=candidate"))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair-runs", type=int, default=5)
    parser.add_argument("--room-runs", type=int, default=3)
    parser.add_argument("--out", type=Path, default=HERE / "results" / "measurements.json")
    args = parser.parse_args()
    connector = os.environ.get("KAKERA_CONNECT")
    if not connector:
        parser.error("set KAKERA_CONNECT")
    with tempfile.TemporaryDirectory(prefix="courier-measure-") as tmp:
        tmp = Path(tmp)
        mailbox = Mailbox(tmp)
        try:
            pairs, rooms = [], []
            for n in range(args.pair_runs):
                workdir = tmp / f"pair{n}"
                workdir.mkdir()
                pairs.append(pair_run(connector, mailbox.url, workdir))
            for n in range(args.room_runs):
                workdir = tmp / f"room{n}"
                workdir.mkdir()
                rooms.append(room_run(connector, mailbox.url, workdir))
            wan = wan_estimate(tmp / "pair0" / "h" / "invite.txt")
        finally:
            mailbox.close()
    result = {
        "note": "loopback-only kakera-connect, local mailbox; not a WAN observation",
        "pair": pairs,
        "room": rooms,
        "pair_typed_to_connected_median_s": statistics.median(r["typed_to_connected_s"] for r in pairs),
        "room_typed_to_connected_median_s": statistics.median(r["typed_to_connected_s"] for r in rooms),
        "wan_invite_estimate": wan,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
