"""English syntax regressions; Japanese comments, paths and display text remain data.

The Markdown check is lexical only: it does not claim that the proposed v1
language is implemented by the v0 compiler.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import kitc  # noqa: E402


class EnglishSyntax(unittest.TestCase):
    def test_accepted_words_are_ascii(self):
        for words in (kitc.MOVE_ALIASES, kitc.PROP_ALIASES, kitc.HEADER_ALIASES):
            for name, canonical in words.items():
                with self.subTest(name=name):
                    self.assertTrue(name.isascii())
                    self.assertTrue(canonical.isascii())

    def test_all_canonical_move_headers_parse(self):
        for name in (
            "main", "melee", "sub_shot", "special_shot", "special_melee",
            "charge_shot", "down_melee",
        ):
            with self.subTest(name=name):
                sheet = kitc.parse(f"kit rena\n{name}\n")
                self.assertEqual(sheet.blocks[0].name, name)
                kitc.compile_text(f"kit rena\n{name}\n")

    def test_japanese_headers_are_rejected_with_replacements(self):
        headers = {
            "メイン": "main", "格闘": "melee", "サブ": "sub_shot",
            "特射": "special_shot", "特格": "special_melee",
            "射CS": "charge_shot", "下格": "down_melee",
            "下格闘": "down_melee", "システム": "system",
        }
        for old, replacement in headers.items():
            with self.subTest(old=old):
                with self.assertRaises(kitc.KitError) as caught:
                    kitc.compile_text(f"kit rena\n{old}\n")
                self.assertIn("2 行目", str(caught.exception))
                self.assertIn(f"`{replacement}`", str(caught.exception))

    def test_japanese_properties_are_rejected_even_on_disabled_layers(self):
        properties = {
            "演目": ("perf", "nata.backstep_shot / nata.air_shot"),
            "慣性": ("inertia", "own"),
            "弾": ("ammo", "none"),
            "ブースト": ("boost", "whole:30"),
            "キャンセル": ("cancel", "main"),
            "空中": ("air", "keep"),
            "虹ステ": ("rainbow", "air"),
        }
        for old, (replacement, value) in properties.items():
            with self.subTest(old=old):
                with self.assertRaises(kitc.KitError) as caught:
                    kitc.compile_text(f"kit rena\nsub_shot\n  {old} {value}\n")
                self.assertIn("3 行目", str(caught.exception))
                self.assertIn(f"`{replacement}`", str(caught.exception))

    def test_japanese_comments_do_not_change_output(self):
        plain = "kit rena\nsub_shot\n  ammo depleted/3/240/180\nsystem\n  ammo\n"
        annotated = (
            "# サブの弾倉\nkit rena\nsub_shot # メイン・特格\n"
            "  ammo depleted/3/240/180 # 慣性、演目、空中\nsystem\n  ammo\n"
        )
        a, b = kitc.compile_text(plain), kitc.compile_text(annotated)
        self.assertEqual(a.env, b.env)
        self.assertEqual(a.files, b.files)
        self.assertEqual(a.digest(), b.digest())

    def test_japanese_file_paths_are_data_not_syntax(self):
        result = kitc.compile_text(
            "kit rena\nsub_shot\n  inertia own\n"
            "system\n  inertia file=設定/慣性.txt\n"
        )
        self.assertEqual(result.env["SAIKAI_INERTIA"], "@設定/慣性.txt")
        self.assertIn("sub_shot=own\n", result.files["設定/慣性.txt"])

    def test_existing_ascii_cs_alias_is_unchanged(self):
        a = kitc.compile_text("kit rena\nCS\n")
        b = kitc.compile_text("kit rena\ncharge_shot\n")
        self.assertEqual(a.env, b.env)

    def test_all_v0_examples_use_english_syntax_and_compile(self):
        examples = sorted((ROOT / "examples").glob("*.kit"))
        self.assertTrue(examples)
        for path in examples:
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                for _, _, words, _ in kitc.read_lines(source):
                    self.assertTrue(all(word.isascii() for word in words), words)
                kitc.compile_text(source)

    def test_design_syntax_blocks_are_ascii_outside_labels_and_comments(self):
        # Diagrams and prose also use text fences. Select syntax samples by
        # their first word, including removed spellings so regressions fail.
        heads = {
            "format", "kit", "for", "move", "resource", "bind", "unbind",
            "observe", "cancel", "followup", "transition", "retime",
            "frames", "animation", "motion", "tune", "kitc",
            *kitc.MOVE_ALIASES, *kitc.JAPANESE_MIGRATIONS,
        }
        paths = [ROOT / "README.md", *sorted((ROOT / "design").glob("*.md"))]
        checked = 0
        for path in paths:
            source = path.read_text(encoding="utf-8")
            for block in re.findall(r"^```(?:text|kit)\n(.*?)^```", source, re.M | re.S):
                # Match strings before comments so a # inside a label stays data.
                syntax = re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*', "", block)
                words = syntax.split()
                if words and words[0] in heads:
                    with self.subTest(path=path.name, first=words[0]):
                        self.assertTrue(syntax.isascii(), syntax)
                    checked += 1
        self.assertGreaterEqual(checked, 19)


if __name__ == "__main__":
    unittest.main()
