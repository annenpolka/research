"""Public input naming is distinct from native performance and backend names."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import kitc  # noqa: E402


class UpAndBoostDash(unittest.TestCase):
    def test_melee_commands_keep_distinct_identities(self):
        names = ["neutral_melee", "up_melee", "side_melee", "down_melee", "boost_dash_melee"]
        source = "kit rena\n" + "\n".join(names) + "\n"
        self.assertEqual([b.name for b in kitc.parse(source).blocks], names)
        self.assertEqual(kitc.compile_text(source).env, kitc.compile_text("kit rena\n").env)

    def test_new_headers_reject_duplicates(self):
        for name in ("up_melee", "boost_dash_melee"):
            with self.subTest(name=name), self.assertRaises(kitc.KitError):
                kitc.parse(f"kit rena\n{name}\n{name}\n")

    def test_new_headers_keep_separate_properties(self):
        sheet = kitc.parse("kit rena\nup_melee\n  boost whole:20\nboost_dash_melee\n  boost whole:40\n")
        self.assertEqual(sheet.blocks[0].lines[0].words, ["boost", "whole:20"])
        self.assertEqual(sheet.blocks[1].lines[0].words, ["boost", "whole:40"])

    def test_new_settings_fail_closed_until_the_controller_is_connected(self):
        props = ("perf nata.front_melee", "inertia own", "ammo none", "boost whole:20",
                 "cancel none", "air keep", "rainbow air", "shots nata.shot")
        systems = ("", "system\n  step\n  loco\n  boost_cost\n  inertia\n  cancel\n  ammo\n")
        for name in ("up_melee", "boost_dash_melee"):
            for prop in props:
                for system in systems:
                    with self.subTest(name=name, prop=prop, enabled=bool(system)):
                        with self.assertRaises(kitc.KitError) as error:
                            kitc.compile_text(f"kit rena\n{name}\n  {prop}\n{system}")
                        self.assertIn("3 行目", str(error.exception))
                        self.assertIn(name, str(error.exception))
                        self.assertIn("unsupported_command_split", str(error.exception))

    def test_down_melee_keeps_its_existing_backend_path(self):
        self.assertNotIn("down_melee", kitc.DIRECTIONAL_MELEE)
        result = kitc.compile_text("kit rena\ndown_melee\n  perf axe.shot / axe.air_shot\n")
        self.assertEqual(result.env["SAIKAI_KIT"], "rena down_melee=axe_main")

    def test_front_back_and_generic_dash_are_not_public_aliases(self):
        for name in ("front_melee", "back_melee", "dash_melee"):
            with self.subTest(name=name), self.assertRaises(kitc.KitError):
                kitc.parse(f"kit rena\n{name}\n")

    def test_native_performance_names_and_main_backend_key_are_preserved(self):
        vocab = kitc.load_vocab()
        for name in ("nata.front_melee", "nata.dash_melee", "nata.air_dash_melee"):
            self.assertIn(name, vocab["perfs"])
        self.assertNotIn("up_melee", kitc.LEGACY_WEAPON_KEYS)
        self.assertNotIn("boost_dash_melee", kitc.LEGACY_WEAPON_KEYS)
        result = kitc.compile_text("kit rena\nmain_shot\n  ammo constant/6/180/120\nsystem\n  ammo\n")
        self.assertEqual(result.env["SAIKAI_AMMO"], "on main=constant/6/180/120")


if __name__ == "__main__":
    unittest.main()
