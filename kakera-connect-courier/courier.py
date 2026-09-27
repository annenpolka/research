#!/usr/bin/env python3
"""kakera courier: one short code instead of two long ones.

daybreak-kakera's connector (kakera-connect) exchanges an invitation and a reply
as files. Today a person copies invite.txt to the other side through a chat,
and copies answer.txt back. This courier does that copying through a
magic-wormhole mailbox. The people exchange only a short code such as
"7-guitarist-revenge", once, from host to joiner.

kakera-connect is not changed. The courier reads and writes the same files a
person would copy (invite.txt / answer.txt, or invite-N.txt / answer-N.txt for a
four-person room). kakera-connect still checks every code itself.

What the mailbox sees: the two couriers' IP addresses, timing and sizes. It
does not see the codes: magic-wormhole runs SPAKE2 on the short code and
encrypts every message with the derived key. A wrong or guessed short code
fails the key agreement (WrongPasswordError) and nothing is sent.

stdout is JSON lines: the connector's own events, forwarded unchanged, and the
courier's events (event names start with "courier_"). Neither contains the short
code or a signal code. The short code goes to short-code.txt (mode 0600) in the
private signal directory, and to stderr for the person at the keyboard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import threading
from pathlib import Path

from twisted.internet import defer, task

import wormhole
from wormhole.errors import WormholeError, WrongPasswordError

PUBLIC_RELAY = "ws://relay.magic-wormhole.io:4000/v1"
# magic-wormhole separates applications by appid. Both sides must use the same.
APPID = "example.invalid/kakera-courier-research/v1"
PROTOCOL = 1
# kakera-connect bounds encoded codes at 96 KiB; the courier refuses more.
MAX_SIGNAL_BYTES = 96 * 1024
SIGNAL_PREFIXES = ("kakera-connect-v1.", "kakera-connect-v2.", "kakera-room-v1.")
SHORT_CODE = re.compile(r"^[0-9]{1,5}(-[a-z]+){2,4}$")
INVITE_FILE = "incoming-invite.txt"
SHORT_CODE_FILE = "short-code.txt"


class CourierError(Exception):
    """A failure with a stable reason code, reported as courier_failed."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def emit(event: dict) -> None:
    sys.stdout.write(json.dumps(event, sort_keys=True) + "\n")
    sys.stdout.flush()


def tell(text: str) -> None:
    """Human-facing line. Never parsed; may contain the short code."""
    sys.stderr.write(text + "\n")
    sys.stderr.flush()


# ---------------------------------------------------------------- files


def build_info(connector: Path) -> dict:
    """Identify the connector build so both sides can refuse a mismatch early.

    The peer's claim is self-reported: this is a courtesy check that turns a
    late "version differs" failure into an immediate message, not security.
    """
    digest = hashlib.sha256(connector.read_bytes()).hexdigest()
    revision = None
    manifest = connector.parent / "manifest.json"
    if manifest.is_file():
        try:
            revision = json.loads(manifest.read_text("utf-8")).get("revision")
        except (OSError, ValueError):
            revision = None
    return {"connector_sha256": digest, "revision": revision}


def publish_private(path: Path, text: str) -> None:
    """Write a one-line file without replacing an existing one.

    Like kakera-connect's own publish: stage, flush, then hard-link the final
    name, so a reader never sees a partial code.
    """
    staging = path.with_name(f".{path.name}.{secrets.token_hex(16)}.tmp")
    fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as handle:
            handle.write(text.rstrip("\n") + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(staging, path)
    finally:
        staging.unlink(missing_ok=True)


def read_signal(path: Path) -> str:
    raw = path.read_bytes()
    if len(raw) > MAX_SIGNAL_BYTES:
        raise CourierError("signal_bounds")
    return check_signal(raw.decode("ascii", "strict").strip())


def check_signal(code: object) -> str:
    """Shape check only. kakera-connect does the real validation."""
    if not isinstance(code, str) or len(code) > MAX_SIGNAL_BYTES:
        raise CourierError("signal_bounds")
    if not code.startswith(SIGNAL_PREFIXES) or any(c.isspace() for c in code):
        raise CourierError("signal_shape")
    return code


def fresh_signal_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for name in (SHORT_CODE_FILE, INVITE_FILE):
        if (path / name).exists():
            raise CourierError("signal_directory_not_empty")


# ------------------------------------------------------------ connector


class ConnectorExited(Exception):
    pass


class Connector:
    """Runs kakera-connect and forwards its JSON events.

    A reader thread hands each stdout line to the reactor thread. Waiters are
    Deferreds that fire on the first matching event, past or future, and fail
    when the connector reports "failed" or exits.

    The process starts on start(), not on construction: the host can hold it
    back until a joiner has typed the short code, so kakera-connect's deadline
    (which covers the code exchange) no longer covers the people.
    """

    def __init__(self, reactor, argv: list[str]):
        self.reactor = reactor
        self.argv = argv
        self.events: list[dict] = []
        self.waiters: list[tuple] = []
        self.proc: subprocess.Popen | None = None
        self.returncode: int | None = None
        self.exited: defer.Deferred = defer.Deferred()
        self.terminal: defer.Deferred = defer.Deferred()

    def start(self) -> None:
        if self.proc is not None:
            return
        self.proc = subprocess.Popen(
            self.argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=None
        )
        emit({"event": "courier_connector_started"})
        threading.Thread(target=self._read, daemon=True).start()

    def finished(self) -> defer.Deferred:
        """Exit code once the process has ended; None if it never started."""
        return self.exited if self.proc is not None else defer.succeed(None)

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for raw in self.proc.stdout:
            self.reactor.callFromThread(self._line, raw)
        code = self.proc.wait()
        self.reactor.callFromThread(self._exit, code)

    def _line(self, raw: bytes) -> None:
        sys.stdout.buffer.write(raw)
        sys.stdout.flush()
        try:
            event = json.loads(raw)
        except ValueError:
            return
        self.events.append(event)
        if event.get("event") == "failed":
            self._end(CourierError("connector_failed", event.get("reason", "")))
            return
        for waiter in list(self.waiters):
            if waiter[0](event):
                self.waiters.remove(waiter)
                waiter[1].callback(event)

    def _end(self, error: Exception) -> None:
        for _, waiter in self.waiters:
            waiter.errback(error)
        self.waiters.clear()
        if not self.terminal.called:
            self.terminal.callback(error)

    def _exit(self, code: int) -> None:
        self.returncode = code
        self._end(ConnectorExited(code))
        self.exited.callback(code)

    def wait_for(self, predicate) -> defer.Deferred:
        for event in self.events:
            if predicate(event):
                return defer.succeed(event)
        if self.returncode is not None:
            return defer.fail(ConnectorExited(self.returncode))
        waiter: defer.Deferred = defer.Deferred()
        self.waiters.append((predicate, waiter))
        return waiter

    def stop(self, signal_dir: Path) -> None:
        """kakera-connect's documented local stop: create stop.txt."""
        if self.proc is not None and self.returncode is None:
            (signal_dir / "stop.txt").touch()


def connector_argv(args, role: str, signal_dir: Path, extra: list[str]) -> list[str]:
    argv = [str(args.connector), role, "--signal-dir", str(signal_dir),
            "--game-port", str(args.game_port), "--timeout-secs", str(args.timeout_secs)]
    if args.stun_url:
        argv += ["--stun-url", args.stun_url]
    return argv + extra


# -------------------------------------------------------------- wormhole


_QUIET = None


def open_wormhole(reactor, args, versions: dict):
    global _QUIET
    if _QUIET is None:
        # magic-wormhole prints progress to stderr, which is the person's console.
        _QUIET = open(os.devnull, "w")  # noqa: SIM115 - lives as long as the process
    return wormhole.create(args.appid, args.relay, reactor, versions=versions, stderr=_QUIET)


def check_peer(peer: dict, ours: dict, *, allow_mismatch: bool) -> dict:
    mine = peer.get("kakera-courier") if isinstance(peer, dict) else None
    if not isinstance(mine, dict) or mine.get("protocol") != PROTOCOL:
        raise CourierError("courier_protocol")
    theirs = mine.get("build") or {}
    if theirs.get("connector_sha256") != ours["connector_sha256"] and not allow_mismatch:
        raise CourierError(
            "build_mismatch",
            f"peer connector {str(theirs.get('connector_sha256'))[:12]} "
            f"revision {theirs.get('revision')}, "
            f"ours {ours['connector_sha256'][:12]} revision {ours['revision']}",
        )
    return mine


def with_timeout(reactor, d: defer.Deferred, seconds: float, reason: str) -> defer.Deferred:
    def expired(failure):
        if failure.check(defer.TimeoutError, defer.CancelledError):
            raise CourierError(reason)
        return failure

    return d.addTimeout(seconds, reactor).addErrback(expired)


def first_of(*deferreds: defer.Deferred) -> defer.Deferred:
    """Fire with (index, result) of the first to finish; errors propagate."""
    d = defer.DeferredList(list(deferreds), fireOnOneCallback=True,
                           fireOnOneErrback=True, consumeErrors=True)

    def unwrap(failure):
        return failure.value.subFailure

    return d.addCallbacks(lambda pair: (pair[1], pair[0]), unwrap)


# ------------------------------------------------------------------ host


async def serve_seat(reactor, args, hole, seat: int, room: bool, conn: Connector,
                     signal_dir: Path, ours: dict) -> None:
    # Waiting for a person to type the code has its own, long bound.
    peer = await with_timeout(reactor, hole.get_versions(), args.peer_wait_secs, "code_timeout")
    check_peer(peer, ours, allow_mismatch=args.allow_build_mismatch)
    emit({"event": "courier_peer_verified", "seat": seat})
    # kakera-connect's own deadline starts here, not when the code was shown.
    conn.start()
    invite_name = f"invite-{seat}.txt" if room else "invite.txt"
    await conn.wait_for(lambda e: e.get("event") == "offer_ready"
                        and e.get("signal_file") == invite_name)
    invite = read_signal(signal_dir / invite_name)
    hole.send_message(json.dumps({"type": "invite", "seat": seat, "code": invite}).encode())
    raw = await with_timeout(reactor, hole.get_message(), args.timeout_secs, "answer_timeout")
    message = json.loads(raw)
    if not isinstance(message, dict) or message.get("type") != "answer":
        raise CourierError("courier_message")
    answer_name = f"answer-{seat}.txt" if room else "answer.txt"
    publish_private(signal_dir / answer_name, check_signal(message.get("code")))
    emit({"event": "courier_answer_delivered", "seat": seat, "signal_file": answer_name})
    await hole.close()


async def run_host(reactor, args) -> int:
    signal_dir = Path(args.signal_dir)
    fresh_signal_dir(signal_dir)
    room = args.participants == 4
    seats = [1, 2, 3] if room else [1]
    ours = build_info(args.connector)
    extra = ["--pregame"] if args.pregame else []
    conn = Connector(reactor, connector_argv(args, "room-host" if room else "host",
                                             signal_dir, extra))
    if args.connector_start == "now":
        conn.start()
    holes = {}
    for seat in seats:
        versions = {"kakera-courier": {"protocol": PROTOCOL, "build": ours,
                                       "mode": "room" if room else "pair",
                                       "seat": seat, "pregame": args.pregame}}
        holes[seat] = open_wormhole(reactor, args, versions)
        holes[seat].allocate_code(args.code_words)
    try:
        codes = {}
        for seat in seats:
            index, code = await first_of(holes[seat].get_code(), conn.terminal)
            if index != 0:
                raise code if isinstance(code, Exception) else CourierError("connector_failed")
            codes[seat] = code
        publish_private(signal_dir / SHORT_CODE_FILE,
                        "\n".join(f"{seat}\t{codes[seat]}" for seat in seats))
        emit({"event": "courier_code_ready", "seats": seats})
        for seat in seats:
            label = f"参加者{seat + 1}" if room else "参加側"
            tell(f"{label}へ伝える合言葉: {codes[seat]}")
        work = defer.gatherResults(
            [defer.ensureDeferred(serve_seat(reactor, args, holes[s], s, room, conn,
                                             signal_dir, ours)) for s in seats],
            consumeErrors=True)
        work.addErrback(lambda f: f.value.subFailure if hasattr(f.value, "subFailure") else f)
        index, result = await first_of(work, conn.terminal)
        if index != 0:
            # The connector ended before every answer arrived.
            raise result if isinstance(result, Exception) else CourierError("connector_failed")
        emit({"event": "courier_done", "seats": seats})
    except (CourierError, WormholeError, ValueError) as error:
        fail(error)
        conn.stop(signal_dir)
        await close_all(holes.values())
        await conn.finished()
        return 1
    return await conn.finished()


async def close_all(holes) -> None:
    for hole in holes:
        try:
            await hole.close()
        except Exception:  # noqa: BLE001 - closing after a failure is best effort
            pass


def fail(error: Exception) -> None:
    if isinstance(error, WrongPasswordError):
        reason, detail = "code_mismatch", "short code differs, or someone else tried it"
    elif isinstance(error, CourierError):
        reason, detail = error.reason, error.detail
    elif isinstance(error, WormholeError):
        reason, detail = "mailbox_" + type(error).__name__, ""
    else:
        reason, detail = "courier_" + type(error).__name__, ""
    emit({"event": "courier_failed", "reason": reason})
    if detail:
        tell(f"courier: {reason}: {detail}")


# ------------------------------------------------------------------ join


async def run_join(reactor, args) -> int:
    code = args.code.strip()
    if not SHORT_CODE.match(code):
        fail(CourierError("short_code_format"))
        return 2
    signal_dir = Path(args.signal_dir)
    fresh_signal_dir(signal_dir)
    ours = build_info(args.connector)
    hole = open_wormhole(reactor, args, {"kakera-courier": {"protocol": PROTOCOL,
                                                            "build": ours}})
    hole.set_code(code)
    conn = None
    try:
        peer = await with_timeout(reactor, hole.get_versions(), args.timeout_secs, "code_timeout")
        host = check_peer(peer, ours, allow_mismatch=args.allow_build_mismatch)
        room = host.get("mode") == "room"
        emit({"event": "courier_peer_verified", "seat": host.get("seat"),
              "mode": host.get("mode")})
        raw = await with_timeout(reactor, hole.get_message(), args.timeout_secs, "invite_timeout")
        message = json.loads(raw)
        if not isinstance(message, dict) or message.get("type") != "invite":
            raise CourierError("courier_message")
        invite_path = signal_dir / INVITE_FILE
        publish_private(invite_path, check_signal(message.get("code")))
        # The joiner does not choose pair/room or --pregame: the host's courier
        # said which, inside the encrypted channel.
        extra = ["--invite", str(invite_path)] + (["--pregame"] if host.get("pregame") else [])
        conn = Connector(reactor, connector_argv(args, "room-join" if room else "join",
                                                 signal_dir, extra))
        conn.start()
        await conn.wait_for(lambda e: e.get("event") == "answer_ready")
        answer = read_signal(signal_dir / "answer.txt")
        hole.send_message(json.dumps({"type": "answer", "code": answer}).encode())
        await hole.close()
        emit({"event": "courier_done", "seat": host.get("seat")})
    except (CourierError, WormholeError, ConnectorExited, ValueError) as error:
        if not isinstance(error, ConnectorExited):
            fail(error)
        await close_all([hole])
        if conn is None:
            return 1
        conn.stop(signal_dir)
        await conn.finished()
        return 1
    return await conn.finished()


# ------------------------------------------------------------------- cli


def parse(argv: list[str]):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="role", required=True)
    for role in ("host", "join"):
        p = sub.add_parser(role)
        p.add_argument("--connector", type=Path, required=True,
                       help="kakera-connect executable (unchanged)")
        p.add_argument("--signal-dir", required=True, help="fresh private directory")
        p.add_argument("--game-port", type=int, required=True)
        p.add_argument("--stun-url", help="passed to kakera-connect (none = loopback test)")
        p.add_argument("--timeout-secs", type=int, default=300)
        p.add_argument("--relay", default=PUBLIC_RELAY, help="magic-wormhole mailbox URL")
        p.add_argument("--appid", default=APPID)
        p.add_argument("--allow-build-mismatch", action="store_true",
                       help="skip the connector hash comparison (tests only)")
        if role == "host":
            p.add_argument("--participants", type=int, choices=(2, 4), default=2)
            p.add_argument("--pregame", action="store_true")
            p.add_argument("--code-words", type=int, default=2)
            p.add_argument("--peer-wait-secs", type=int, default=1800,
                           help="how long the short code waits for a joiner")
            p.add_argument("--connector-start", choices=("peer", "now"), default="peer",
                           help="peer: start kakera-connect when the first joiner "
                                "has typed the code (its deadline then excludes the "
                                "people); now: at once, as a person would today")
        else:
            p.add_argument("--code", required=True, help="short code from the host")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout_secs <= 600:
        parser.error("--timeout-secs must be 1..600, as in kakera-connect")
    if args.role == "host" and not 1 <= args.peer_wait_secs <= 86400:
        parser.error("--peer-wait-secs must be 1..86400")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse(sys.argv[1:] if argv is None else argv)
    result = {}

    async def entry(reactor):
        runner = run_host if args.role == "host" else run_join
        result["code"] = await runner(reactor, args)

    try:
        task.react(lambda reactor: defer.ensureDeferred(entry(reactor)))
    except SystemExit:
        pass
    return result.get("code", 1)


if __name__ == "__main__":
    sys.exit(main())
