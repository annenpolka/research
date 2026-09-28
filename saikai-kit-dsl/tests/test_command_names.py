"""Public command names must not leak into or collapse in the legacy backend."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import kitc  # noqa: E402


class CommandNames(unittest.TestCase):
    def test_public_headers_keep_distinct_identities(self):
        names = ["main_shot", "neutral_melee", "side_melee"]
        sheet = kitc.parse("kit rena\n" + "\n".join(names) + "\n")
        self.assertEqual([block.name for block in sheet.blocks], names)
        self.assertNotIn("main", kitc.MOVE_ALIASES)
        self.assertNotIn("melee", kitc.MOVE_ALIASES)

    def test_melee_blocks_do_not_share_their_properties(self):
        sheet = kitc.parse(
            "kit rena\nneutral_melee\n  boost whole:20\n"
            "side_melee\n  boost whole:40\n"
        )
        self.assertEqual(sheet.blocks[0].lines[0].words, ["boost", "whole:20"])
        self.assertEqual(sheet.blocks[1].lines[0].words, ["boost", "whole:40"])
        self.assertNotEqual(sheet.blocks[0].name, sheet.blocks[1].name)

    def test_duplicate_directional_headers_are_still_rejected(self):
        for name in ("neutral_melee", "side_melee"):
            with self.subTest(name=name), self.assertRaises(kitc.KitError):
                kitc.parse(f"kit rena\n{name}\n{name}\n")

    def test_old_main_header_has_a_migration_hint(self):
        with self.assertRaises(kitc.KitError) as error:
            kitc.compile_text("kit rena\nmain\n")
        self.assertIn("2 行目", str(error.exception))
        self.assertIn("`main_shot`", str(error.exception))

    def test_old_melee_is_not_silently_renamed_to_neutral(self):
        with self.assertRaises(kitc.KitError) as error:
            kitc.compile_text("kit rena\nmelee\n")
        message = str(error.exception)
        for required in ("2 行目", "neutral_melee", "side_melee", "単純置換しない"):
            self.assertIn(required, message)

    def test_main_shot_uses_the_legacy_ammo_key(self):
        result = kitc.compile_text(
            "kit rena\nmain_shot\n  ammo constant/6/180/120\nsystem\n  ammo\n"
        )
        self.assertEqual(result.env["SAIKAI_AMMO"], "on main=constant/6/180/120")
        self.assertEqual(result.provenance[-1].what, "main_shot=constant/6/180/120")

    def test_main_shot_uses_the_legacy_inertia_key(self):
        result = kitc.compile_text(
            "kit rena\nmain_shot\n  inertia stop:60/80/85\nsystem\n  inertia\n"
        )
        rows = dict(kitc.split_table(result.env["SAIKAI_INERTIA"]))
        self.assertEqual(rows["main"], "stop:60/80/85")
        self.assertEqual(rows["melee"], "own")
        self.assertNotIn("main_shot", rows)

    def test_main_shot_boost_keeps_the_original_performance_ids(self):
        result = kitc.compile_text(
            "kit rena\nmain_shot\n  boost whole:20\n"
            "system\n  step\n  loco\n  boost_cost\n"
        )
        rows = dict(kitc.split_table(result.env["SAIKAI_BOOST_COST"]))
        self.assertEqual(rows, dict.fromkeys(kitc.load_vocab()["bases"]["rena"]["mains"], "whole:20"))

    def test_main_shot_cancel_dry_and_shots_use_legacy_output(self):
        result = kitc.compile_text(
            "kit rena\nmain_shot\n  shots nata.shot\n"
            "sub_shot\n  cancel main_shot dry\nsystem\n  cancel\n"
        )
        self.assertEqual(result.env["SAIKAI_CANCEL"], "on from=nata.shot except=sub_shot")

    def test_old_cancel_source_is_rejected_even_without_the_layer(self):
        for suffix in ("", " dry"):
            with self.subTest(suffix=suffix), self.assertRaises(kitc.KitError) as error:
                kitc.compile_text(f"kit rena\nsub_shot\n  cancel main{suffix}\n")
            self.assertIn("3 行目", str(error.exception))
            self.assertIn("cancel main_shot", str(error.exception))

    def test_duplicate_legacy_ammo_key_is_detected_after_translation(self):
        with self.assertRaises(kitc.KitError) as error:
            kitc.compile_text(
                "kit rena\nmain_shot\n  ammo none\nsystem\n  ammo main=never/1/1\n"
            )
        self.assertIn("両方", str(error.exception))

    def test_directional_settings_fail_closed_until_connected(self):
        properties = (
            "perf nata.melee", "inertia own", "ammo none", "boost whole:20",
            "cancel none", "air keep", "rainbow air", "shots nata.shot",
        )
        for name in ("neutral_melee", "side_melee"):
            for prop in properties:
                for system in ("", "system\n  step\n  loco\n  boost_cost\n  inertia\n  cancel\n  ammo\n"):
                    with self.subTest(name=name, prop=prop, enabled=bool(system)):
                        with self.assertRaises(kitc.KitError) as error:
                            kitc.compile_text(f"kit rena\n{name}\n  {prop}\n{system}")
                        self.assertIn("3 行目", str(error.exception))
                        self.assertIn(name, str(error.exception))
                        self.assertIn("unsupported_command_split", str(error.exception))

    def test_system_melee_is_not_a_move_header(self):
        result = kitc.compile_text("kit rena\nsystem\n  melee side=on\n")
        self.assertEqual(result.env["SAIKAI_MELEE"], "on side=on")

    def test_data_containing_the_old_words_is_not_rewritten(self):
        result = kitc.compile_text(
            "kit rena\nmain_shot\n  inertia own\n"
            "system\n  inertia file=main/melee.txt\n"
        )
        self.assertEqual(result.env["SAIKAI_INERTIA"], "@main/melee.txt")
        self.assertIn("main=own\n", result.files["main/melee.txt"])

    def test_active_documentation_uses_new_public_names(self):
        # Historical prose/backend keys/native PerfIds are intentionally not renamed.
        paths = [ROOT / "README.md", *sorted((ROOT / "design").glob("*.md"))]
        forbidden = re.compile(
            r"^(?:main|melee)(?:\s|$)|\binput=(?:main|melee)\b|"
            r"^(?:bind|unbind)\s+(?:main|melee)\b|^\s*cancel\s+main\b", re.M
        )
        for path in paths:
            for block in re.findall(r"^```(?:text|kit)\n(.*?)^```", path.read_text(), re.M | re.S):
                syntax = re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*', "", block)
                with self.subTest(path=path.name):
                    self.assertIsNone(forbidden.search(syntax), syntax)


if __name__ == "__main__":
    unittest.main()
