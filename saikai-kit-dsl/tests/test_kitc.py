"""Tests of the kit sheet compiler (python3 -m unittest discover -s tests -v)."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import kitc  # noqa: E402

# daybreak-saikai experiments/down-melee-axe.md (abe253c), the play setting
# the user plays with (「遊びの設定」, without the effect files, widescreen and HUD).
RECORDED_PLAY = (
    'SAIKAI_COMMANDS=on SAIKAI_KIT="rena down_melee=axe_main" SAIKAI_STEP="on shot=keep" '
    'SAIKAI_LOCO="on parts=bd air=on blend=7" SAIKAI_BOOST_COST=on SAIKAI_GUARD=on '
    'SAIKAI_MELEE="on side=on" SAIKAI_LANDING=on SAIKAI_UKEMI=on SAIKAI_HOMING="on muzzle=aim" '
    'SAIKAI_LOCK=on SAIKAI_AIR=on SAIKAI_INERTIA=on SAIKAI_CHARGE=on SAIKAI_CANCEL=on '
    'SAIKAI_COMBO=on SAIKAI_REACT="on getup=on" SAIKAI_BODY=on SAIKAI_AMMO=on SAIKAI_CAMERA=on'
)


def compile_sheet(text: str) -> kitc.Result:
    return kitc.compile_text(text)


def refused(test: unittest.TestCase, text: str, *needles: str) -> str:
    with test.assertRaises(kitc.KitError) as cm:
        compile_sheet(text)
    message = str(cm.exception)
    for needle in needles:
        test.assertIn(needle, message)
    return message


class PlaySetting(unittest.TestCase):
    def test_the_play_sheet_is_the_recorded_play_setting(self):
        result = compile_sheet((ROOT / "examples/rena-play.kit").read_text(encoding="utf-8"))
        recorded = dict(item.split("=", 1) for item in shlex.split(RECORDED_PLAY))
        self.assertEqual(result.env, recorded)
        self.assertEqual(len(result.env), 20)

    def test_the_hash_depends_on_the_values_only(self):
        a = compile_sheet("kit rena\nsystem\n  guard\n  step\n")
        b = compile_sheet("# 並べ方が違うだけ\nkit rena\nsystem\n  step\n  guard\n")
        self.assertEqual(a.digest(), b.digest())
        c = compile_sheet("kit rena\nsystem\n  step shot=keep\n  guard\n")
        self.assertNotEqual(a.digest(), c.digest())


class Transposition(unittest.TestCase):
    def test_an_inertia_row_goes_over_the_on_table(self):
        # A written SAIKAI_INERTIA table starts from `default=stop` alone: the
        # sheet's row must not drop the `on` table's moving main and melees.
        env = compile_sheet(
            "kit rena\nsub_shot\n  inertia stop:60/80/85\nsystem\n  inertia\n"
        ).env
        rows = dict(item.split("=", 1) for item in env["SAIKAI_INERTIA"].split(";"))
        self.assertEqual(rows["sub_shot"], "stop:60/80/85")
        self.assertEqual(rows["main"], "move")
        self.assertEqual(rows["melee"], "own")
        self.assertEqual(rows["nata.ex"], "own")
        self.assertEqual(rows["default"], "stop:50/92/94")

    def test_a_cap_in_mbon_lengths_is_scaled_by_20_over_3(self):
        env = compile_sheet(
            "kit rena\nsub_shot\n  inertia stop cap=-/4.0mbon\nsystem\n  inertia\n"
        ).env
        self.assertIn("sub_shot=stop:50/92/94 cap=-/26.666667", env["SAIKAI_INERTIA"])

    def test_a_boost_cost_goes_to_each_performance_of_the_move(self):
        env = compile_sheet(
            "kit rena\ndown_melee\n  perf axe.shot / axe.air_shot\n  boost lunge:20\n"
            "system\n  step\n  loco\n  boost_cost\n"
        ).env
        self.assertEqual(env["SAIKAI_BOOST_COST"], "axe.shot=lunge:20;axe.air_shot=lunge:20")

    def test_the_cancel_rows_become_to_and_except(self):
        env = compile_sheet(
            "kit rena\nsub_shot\n  cancel main_shot dry\nspecial_melee\n  cancel none\nsystem\n  cancel\n"
        ).env
        self.assertEqual(
            env["SAIKAI_CANCEL"], "on to=sub_shot,special_shot,down_melee except=sub_shot"
        )

    def test_nothing_is_written_that_equals_the_default(self):
        env = compile_sheet(
            "kit rena\nmain_shot\n  shots nata.shot nata.lever_shot nata.slide_shot_right "
            "nata.slide_shot_left nata.air_dash_shot nata.air_shot\n"
            "sub_shot\n  cancel main_shot\ndown_melee\n  perf axe.shot / axe.air_shot\n  rainbow air\n"
            "system\n  step\n  cancel\n"
        ).env
        self.assertEqual(env["SAIKAI_CANCEL"], "on")
        self.assertEqual(env["SAIKAI_STEP"], "on")

    def test_ammo_and_hp(self):
        env = compile_sheet(
            "kit mion\nhp 9000\nsystem\n  charge\n"
        ).env
        self.assertEqual(env["SAIKAI_HP"], "on mion=9000")
        env = compile_sheet("kit rena\nsub_shot\n  ammo depleted/2/300\nsystem\n  ammo\n").env
        self.assertEqual(env["SAIKAI_AMMO"], "on sub_shot=depleted/2/300")

    def test_a_table_can_go_to_a_file_for_the_reload(self):
        result = compile_sheet(
            "kit rena\nsub_shot\n  inertia own\nsystem\n  inertia file=t.txt\n"
        )
        self.assertEqual(result.env["SAIKAI_INERTIA"], "@t.txt")
        self.assertIn("sub_shot=own\n", result.files["t.txt"])
        self.assertIn("main=move\n", result.files["t.txt"])


class Refusals(unittest.TestCase):
    def test_an_unknown_performance_names_its_line(self):
        refused(self, "kit rena\n\nsub_shot\n  perf nata.bakstep_shot\n", "4 行目", "unknown_performance")

    def test_a_borrow_never_measured_onto_the_base(self):
        refused(self, "kit mion\nspecial_melee\n  perf iron.slide_melee\n", "unmeasured_borrow")

    def test_a_binding_the_kit_setting_cannot_say_needs_v1(self):
        refused(self, "kit rena\nsub_shot\n  perf nata.shot\n", "v1")
        refused(self, "kit mion\nsub_shot\n  perf water.shot\n", "v1")

    def test_the_main_and_the_melees_are_not_the_kits(self):
        refused(self, "kit rena\nmain_shot\n  perf nata.shot\n", "controller")

    def test_a_layer_the_water_gun_has_not_got(self):
        refused(self, "kit mion\nsystem\n  guard\n", "J77", "unsupported_class")
        refused(self, "kit mion\nsystem\n  step\n", "J77")

    def test_the_water_guns_loco_gets_the_steps_hook(self):
        result = compile_sheet("kit mion\nsystem\n  loco\n")
        self.assertEqual(result.env["SAIKAI_STEP"], "on")
        self.assertTrue(any("F188" in n for n in result.notes))

    def test_nata_loco_needs_the_step(self):
        refused(self, "kit rena\nsystem\n  loco\n", "needs_step")

    def test_a_key_the_layer_does_not_have(self):
        refused(self, "kit rena\nsystem\n  step shot=keep sideways=on\n", "sideways")

    def test_one_key_in_two_places(self):
        refused(
            self,
            "kit rena\nsub_shot\n  ammo none\nsystem\n  ammo sub_shot=never/1/1\n",
            "両方",
        )

    def test_cancel_with_no_move_left(self):
        text = "kit rena\n" + "".join(
            f"{m}\n  cancel none\n" for m in ("sub_shot", "special_shot", "special_melee", "down_melee")
        ) + "system\n  cancel\n"
        refused(self, text, "to=none")

    def test_a_run_needs_a_mark_on_every_value(self):
        refused(self, "kit rena\nfor run\nsystem\n  guard\n", "for run")
        result = compile_sheet("kit rena\nfor run\nsystem\n  guard  ?U13\n")
        self.assertEqual(result.provenance[0].mark, "?U13")

    def test_a_malformed_mark(self):
        refused(self, "kit rena\nsystem\n  guard !9\n", "印")

    def test_too_many_donor_classes(self):
        # Not reachable through today's rena kit (it borrows two classes at
        # most), so the vocabulary is narrowed to one donor for the test.
        vocab = kitc.load_vocab()
        vocab["max_donor_classes"] = 1
        sheet = kitc.parse("kit rena\ndown_melee\n  perf axe.shot / axe.air_shot\n")
        with self.assertRaises(kitc.KitError) as cm:
            kitc.Compiler(sheet, vocab).compile()
        self.assertIn("too_many_donors", str(cm.exception))


class Notes(unittest.TestCase):
    def test_air_says_which_air_performances_are_not_played(self):
        result = compile_sheet("kit rena\nsub_shot\n  air keep\nsystem\n  air\n")
        self.assertEqual(result.env["SAIKAI_AIR"], "on keep=nata.air_shot")
        joined = "\n".join(result.notes)
        self.assertNotIn("`sub_shot` は空中でも", joined)
        self.assertIn("`special_shot` は空中でも地上の nata.full_charge_shot", joined)

    def test_a_row_for_a_layer_that_is_off_is_a_warning(self):
        result = compile_sheet("kit rena\nsub_shot\n  ammo none\n")
        self.assertNotIn("SAIKAI_AMMO", result.env)
        self.assertTrue(any("効かない" in w for w in result.warnings))


def oracle_available() -> bool:
    return (
        shutil.which("cargo") is not None
        and os.environ.get("KITC_ORACLE") == "1"
    )


@unittest.skipUnless(oracle_available(), "KITC_ORACLE=1 と cargo（toolchain 1.97.1）が要る")
class Oracle(unittest.TestCase):
    """Every value kitc writes for a layer saikai-rules parses is accepted by
    saikai-rules itself (oracle/run.sh clones saikai at vocab.json's commit)."""

    def test_every_example_parses_with_saikai_rules(self):
        lines = []
        for path in sorted((ROOT / "examples").glob("*.kit")):
            result = compile_sheet(path.read_text(encoding="utf-8"))
            for var, value in result.env.items():
                if value.startswith("@"):
                    body = result.files[value[1:]].split("\n", 1)[1]
                    value = ";".join(line for line in body.splitlines() if line)
                lines.append(f"{var}\t{value}")
        out = subprocess.run(
            [str(ROOT / "oracle/run.sh")],
            input="\n".join(lines) + "\n",
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        checked = [line for line in out if "no rules parser" not in line]
        self.assertGreater(len(checked), 20)
        for line in checked:
            self.assertEqual(line.split("\t")[1], "ok", line)


if __name__ == "__main__":
    unittest.main()
