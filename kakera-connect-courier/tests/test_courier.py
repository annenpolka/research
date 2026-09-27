"""End-to-end checks of the courier with the real, unchanged kakera-connect.

Needs:
  KAKERA_CONNECT=/path/to/kakera-connect  (built from daybreak-kakera; skipped if unset)
  magic-wormhole and magic-wormhole-mailbox-server (a local mailbox is started;
  the public mailbox is never used by these tests)

Every connection is kakera-connect's loopback-only test mode (--stun-url none),
so these are local observations, not NAT traversal.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
COURIER = HERE / "courier.py"
sys.path.insert(0, str(HERE))
import courier  # noqa: E402
from harness import Mailbox, Proc, free_port  # noqa: E402

CONNECTOR = os.environ.get("KAKERA_CONNECT")
SECRET_SHAPES = re.compile(r"kakera-(connect|room)-v[0-9]+\.")


@unittest.skipUnless(CONNECTOR and Path(CONNECTOR).is_file(), "set KAKERA_CONNECT")
class CourierEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="courier-e2e-"))
        cls.mailbox = Mailbox(cls.tmp)
        cls.relay = cls.mailbox.url

    @classmethod
    def tearDownClass(cls):
        cls.mailbox.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(dir=self.tmp))
        self.procs: list[Proc] = []

    def tearDown(self):
        for p in self.procs:
            p.close()

    def courier(self, role, signal, port, *extra, connector=None):
        argv = [sys.executable, str(COURIER), role, "--connector", connector or CONNECTOR,
                "--signal-dir", str(self.dir / signal), "--game-port", str(port),
                "--stun-url", "none", "--timeout-secs", "60", "--relay", self.relay, *extra]
        p = Proc(argv, self.dir)
        self.procs.append(p)
        return p

    def short_codes(self, signal, count):
        path = self.dir / signal / courier.SHORT_CODE_FILE
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not path.exists():
            time.sleep(0.05)
        rows = [line.split("\t") for line in path.read_text().splitlines()]
        self.assertEqual(len(rows), count)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        return {int(seat): code for seat, code in rows}

    def assert_no_secrets(self, proc, codes):
        out = "".join(proc.lines)
        self.assertIsNone(SECRET_SHAPES.search(out), "a signal code reached stdout")
        for code in codes:
            self.assertNotIn(code, out, "the short code reached stdout")

    def stop(self, *signals):
        for signal in signals:
            (self.dir / signal / "stop.txt").touch()

    # ------------------------------------------------------------ pair

    def test_pair_connects_with_one_short_code_and_carries_game_datagrams(self):
        g0, g1 = free_port(socket.SOCK_DGRAM), free_port(socket.SOCK_DGRAM)
        host = self.courier("host", "h", g0)
        code = self.short_codes("h", 1)[1]
        self.assertRegex(code, courier.SHORT_CODE)
        # The joiner types the short code. It does not choose pair or room.
        join = self.courier("join", "j", g1, "--code", code)
        h = host.wait_event("connected")
        j = join.wait_event("connected")
        self.assertEqual(h["session"], j["session"])

        # A game datagram through both bridges, in each direction.
        session = bytes.fromhex(h["session"])
        a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        a.bind(("127.0.0.1", g0))
        b.bind(("127.0.0.1", g1))
        b.settimeout(5)
        a.settimeout(5)
        a.sendto(b"KKP2P001" + session + bytes([0, 1]) + b"from host", ("127.0.0.1", h["bridge_port"]))
        data, _ = b.recvfrom(8192)
        self.assertTrue(data.endswith(b"from host"))
        b.sendto(b"KKP2P001" + session + bytes([1, 1]) + b"from join", ("127.0.0.1", j["bridge_port"]))
        data, _ = a.recvfrom(8192)
        self.assertTrue(data.endswith(b"from join"))
        a.close()
        b.close()

        self.stop("h", "j")
        self.assertEqual(host.wait(), 0, host.stderr)
        self.assertEqual(join.wait(), 0, join.stderr)
        self.assertIn("closed", host.names())
        self.assertIn("closed", join.names())
        self.assert_no_secrets(host, [code])
        self.assert_no_secrets(join, [code])
        # The joiner's copy of the invite is private, like kakera-connect's own files.
        self.assertEqual((self.dir / "j" / courier.INVITE_FILE).stat().st_mode & 0o777, 0o600)

    def test_pregame_follows_the_host(self):
        host = self.courier("host", "h", free_port(socket.SOCK_DGRAM), "--pregame")
        code = self.short_codes("h", 1)[1]
        join = self.courier("join", "j", free_port(socket.SOCK_DGRAM), "--code", code)
        self.assertIn("pregame", host.wait_event("connected"))
        self.assertIn("pregame", join.wait_event("connected"))
        self.stop("h", "j")
        self.assertEqual(host.wait(), 0)
        self.assertEqual(join.wait(), 0)

    # ------------------------------------------------------------ room

    def test_room_of_four_connects_with_three_short_codes(self):
        host = self.courier("host", "r0", free_port(socket.SOCK_DGRAM), "--participants", "4")
        codes = self.short_codes("r0", 3)
        joins = [self.courier("join", f"r{seat}", free_port(socket.SOCK_DGRAM),
                              "--code", codes[seat]) for seat in (1, 2, 3)]
        self.assertEqual(host.wait_event("connected", 90)["ready_edges"], 6)
        for seat, join in zip((1, 2, 3), joins, strict=True):
            event = join.wait_event("connected", 90)
            self.assertEqual(event["ready_edges"], 6)
            self.assertEqual(event["participant"], seat)
        self.stop("r0", "r1", "r2", "r3")
        for p in [host, *joins]:
            self.assertEqual(p.wait(), 0, p.stderr)
            self.assert_no_secrets(p, codes.values())

    # --------------------------------------------------------- refusals

    def test_a_wrong_code_fails_both_sides_before_the_joiner_starts_a_connector(self):
        host = self.courier("host", "h", free_port(socket.SOCK_DGRAM))
        code = self.short_codes("h", 1)[1]
        nameplate = code.split("-")[0]
        wrong = f"{nameplate}-aardvark-absurd"
        self.assertNotEqual(wrong, code)
        join = self.courier("join", "j", free_port(socket.SOCK_DGRAM), "--code", wrong)
        self.assertEqual(join.wait_event("courier_failed")["reason"], "code_mismatch")
        self.assertEqual(host.wait_event("courier_failed")["reason"], "code_mismatch")
        self.assertEqual(join.wait(), 1)
        self.assertEqual(host.wait(), 1)
        # Nothing was started anywhere: the host holds its connector until a
        # joiner has proven the code, and the joiner never received an invite.
        self.assertNotIn("courier_connector_started", host.names())
        self.assertNotIn("courier_connector_started", join.names())
        self.assertFalse((self.dir / "j" / courier.INVITE_FILE).exists())

    def test_a_different_connector_build_is_refused_before_connecting(self):
        other = self.dir / "kakera-connect-other"
        shutil.copy2(CONNECTOR, other)
        with open(other, "ab") as handle:
            handle.write(b"\0")  # a different hash; the ELF still runs
        host = self.courier("host", "h", free_port(socket.SOCK_DGRAM))
        code = self.short_codes("h", 1)[1]
        join = self.courier("join", "j", free_port(socket.SOCK_DGRAM), "--code", code,
                            connector=str(other))
        self.assertEqual(join.wait_event("courier_failed")["reason"], "build_mismatch")
        self.assertEqual(host.wait_event("courier_failed")["reason"], "build_mismatch")
        self.assertEqual(join.wait(), 1)
        self.assertEqual(host.wait(), 1)
        self.assertNotIn("courier_connector_started", join.names())
        self.assertNotIn("courier_connector_started", host.names())
        self.assertIn("revision", join.stderr)

    # ------------------------------------------------------- deadlines

    def test_today_the_connector_deadline_runs_while_the_code_is_passed(self):
        # --connector-start now reproduces today's order: kakera-connect starts
        # when the invitation is made, and its deadline covers the people.
        host = self.courier("host", "h", free_port(socket.SOCK_DGRAM),
                            "--connector-start", "now", "--timeout-secs", "3")
        self.short_codes("h", 1)
        self.assertEqual(host.wait_event("failed", 30)["reason"], "connect_timeout")
        self.assertEqual(host.wait_event("courier_failed")["reason"], "connector_failed")
        self.assertEqual(host.wait(), 1)

    def test_a_joiner_later_than_the_connector_deadline_still_connects(self):
        host = self.courier("host", "h", free_port(socket.SOCK_DGRAM), "--timeout-secs", "3")
        code = self.short_codes("h", 1)[1]
        time.sleep(5)  # longer than kakera-connect's deadline
        self.assertNotIn("courier_connector_started", host.names())
        join = self.courier("join", "j", free_port(socket.SOCK_DGRAM), "--code", code,
                            "--timeout-secs", "3")
        host.wait_event("connected")
        join.wait_event("connected")
        self.stop("h", "j")
        self.assertEqual(host.wait(), 0)
        self.assertEqual(join.wait(), 0)

    def test_a_used_code_leaves_a_late_joiner_waiting_until_its_deadline(self):
        # magic-wormhole releases the nameplate once two sides are in, so a
        # third person with the same code is not refused: they wait alone.
        host = self.courier("host", "h", free_port(socket.SOCK_DGRAM))
        code = self.short_codes("h", 1)[1]
        first = self.courier("join", "j", free_port(socket.SOCK_DGRAM), "--code", code)
        host.wait_event("connected")
        first.wait_event("connected")
        late = self.courier("join", "late", free_port(socket.SOCK_DGRAM), "--code", code,
                            "--timeout-secs", "3")
        self.assertEqual(late.wait_event("courier_failed", 30)["reason"], "code_timeout")
        self.assertEqual(late.wait(), 1)
        self.assertNotIn("courier_connector_started", late.names())
        self.stop("h", "j")
        self.assertEqual(host.wait(), 0)
        self.assertEqual(first.wait(), 0)

    def test_a_malformed_short_code_is_refused_without_the_mailbox(self):
        join = self.courier("join", "j", free_port(socket.SOCK_DGRAM), "--code", "kakera-connect-v2.AAAA")
        self.assertEqual(join.wait_event("courier_failed")["reason"], "short_code_format")
        self.assertEqual(join.wait(), 2)


class SignalShape(unittest.TestCase):
    def test_shape_check_is_only_a_shape_check(self):
        self.assertEqual(courier.check_signal("kakera-connect-v2.abc"), "kakera-connect-v2.abc")
        self.assertEqual(courier.check_signal("kakera-room-v1.abc"), "kakera-room-v1.abc")
        for bad in ["", "kakera-connect-v2.a b", "http://x", None, "kakera-connect-v2." + "a" * 100_000]:
            with self.assertRaises(courier.CourierError):
                courier.check_signal(bad)

    def test_publish_never_replaces_a_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "answer.txt"
            courier.publish_private(path, "kakera-connect-v2.first")
            with self.assertRaises(FileExistsError):
                courier.publish_private(path, "kakera-connect-v2.second")
            self.assertEqual(path.read_text(), "kakera-connect-v2.first\n")
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["answer.txt"])

    def test_short_code_pattern(self):
        for good in ["7-guitarist-revenge", "123-a-b", "4-one-two-three"]:
            self.assertRegex(good, courier.SHORT_CODE)
        for bad in ["guitarist-revenge", "7-", "7-Guitarist-revenge", "7 guitarist revenge"]:
            self.assertNotRegex(bad, courier.SHORT_CODE)


if __name__ == "__main__":
    unittest.main()
