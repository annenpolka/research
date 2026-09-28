#!/usr/bin/env python3
"""kitc: a prototype compiler for a human-facing kit sheet of daybreak-saikai.

A kit sheet (`*.kit`) is written move by move, the way a player thinks of a
kit (the sub: what it plays, how it carries momentum, its magazine, whether
it cancels the main). Saikai reads its settings layer by layer instead
(`SAIKAI_INERTIA`, `SAIKAI_AMMO`, `SAIKAI_CANCEL`, ...), each with its own
small grammar. kitc transposes the sheet into those `SAIKAI_*` values, so
the sheet runs on today's saikai without any change to its Rust code (v0).

Checks made before the game ever starts:

- names: every performance, move, layer and option key is from the
  vocabulary (vocab.json, a snapshot of saikai abe253c);
- the base: a layer the base class does not support yet is refused
  (saikai J77); a performance of another class needs a measured borrow onto
  the base, and at most two donor classes;
- dependencies the runtime has but does not explain (the loco needs the
  step's hook, even on the water gun where the step itself is refused);
- the tables' override rules: a written `SAIKAI_INERTIA` table starts from
  nothing but `default=stop`, a written `SAIKAI_BOOST_COST` table starts from
  the `on` table; kitc always starts from the `on` table;
- provenance: `!J<n>` marks a user decision, `?U<n>` or `?` a proposal.
  `for run` refuses an unmarked line (a run record must say which values
  were decided); `for play` only counts them.

Standard library only (Python 3.11+). Run `python3 kitc.py --help`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

VOCAB_PATH = Path(__file__).with_name("vocab.json")

# ---------------------------------------------------------------------------
# Syntax uses English/ASCII words. Japanese remains valid in comments and data.

MOVE_ALIASES = {
    "main": "main",
    "melee": "melee",
    "sub_shot": "sub_shot",
    "special_shot": "special_shot",
    "special_melee": "special_melee",
    "charge_shot": "charge_shot",
    "CS": "charge_shot",
    "down_melee": "down_melee",
}
# The weapon rows that are not kit moves: the original's controller plays them.
WEAPON_ROWS = ("main", "melee")

PROP_ALIASES = {
    "perf": "perf",
    "inertia": "inertia",
    "ammo": "ammo",
    "boost": "boost",
    "cancel": "cancel",
    "air": "air",
    "rainbow": "rainbow",
    "shots": "shots",
}

HEADER_ALIASES = {
    "system": "system",
    "raw": "raw",
}

# Migration hints only: these spellings are rejected, never normalized.
JAPANESE_MIGRATIONS = {
    "メイン": "main",
    "格闘": "melee",
    "サブ": "sub_shot",
    "特射": "special_shot",
    "特格": "special_melee",
    "射CS": "charge_shot",
    "下格": "down_melee",
    "下格闘": "down_melee",
    "演目": "perf",
    "慣性": "inertia",
    "弾": "ammo",
    "ブースト": "boost",
    "キャンセル": "cancel",
    "空中": "air",
    "虹ステ": "rainbow",
    "システム": "system",
}

# The order kitc writes the variables in (the order of saikai's play setting).
ENV_ORDER = (
    "commands", "kit", "step", "loco", "boost_cost", "guard", "melee", "landing",
    "ukemi", "homing", "lock", "air", "inertia", "charge", "cancel", "combo",
    "react", "body", "ammo", "camera", "hp", "hud", "hud_redraw", "friendly",
    "widescreen", "step_fx", "step_ghost", "bd_fx", "gauge",
)

MARK_RE = re.compile(r"^(?:![JU]\d+|\?(?:[JUHN]\d+)?)$")
CARRY_RE = re.compile(r"^(move|own|stop|stop:\d{1,3}/\d{1,3}/\d{1,3})$")
SPEND_RE = re.compile(
    r"^(none|carry|whole:\d+(\+\d+)?|lunge:\d+(\+\d+)?(/\d+)?|window:\d+(\+\d+)?x\d+)$"
)
MAG_RE = re.compile(
    r"^(none|(constant|depleted|never|manual)/\d{1,2}/\d{1,4}(/\d{1,4})?(/wait\d{1,3})?(/hold)?(/norefill)?)$"
)


class KitError(Exception):
    """A sheet kitc refuses, with the line it refuses it at."""


@dataclass
class Line:
    no: int
    words: list[str]
    mark: str | None

    def where(self) -> str:
        return f"{self.no} 行目"


@dataclass
class Block:
    head: Line
    kind: str  # "move", "system", "raw"
    name: str
    lines: list[Line] = field(default_factory=list)


@dataclass
class Provenance:
    var: str
    what: str
    mark: str | None
    line: int


@dataclass
class Result:
    env: dict[str, str]
    files: dict[str, str]
    notes: list[str]
    warnings: list[str]
    provenance: list[Provenance]
    mode: str
    kit: str | None

    def digest(self) -> str:
        text = "".join(f"{k}={v}\n" for k, v in sorted(self.env.items()))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def load_vocab(path: Path = VOCAB_PATH) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Reading the sheet.


def read_lines(text: str) -> list[tuple[int, bool, list[str], str | None]]:
    """(line number, indented, words, mark) for each line with words."""
    out = []
    for no, raw in enumerate(text.splitlines(), start=1):
        body = raw.split("#", 1)[0].rstrip()
        if not body.strip():
            continue
        indented = body[:1] in (" ", "\t", "　")
        words = body.split()
        if words[0] in JAPANESE_MIGRATIONS:
            replacement = JAPANESE_MIGRATIONS[words[0]]
            raise KitError(
                f"{no} 行目：日本語の構文語 `{words[0]}` は使えない。`{replacement}` に置き換える"
            )
        mark = None
        if words and MARK_RE.match(words[-1]):
            mark = words.pop()
        elif any(w[:1] in "!?" and len(w) > 1 for w in words):
            bad = next(w for w in words if w[:1] in "!?" and len(w) > 1)
            raise KitError(f"{no} 行目：印 `{bad}` の形が読めない（`!J9`・`?U14`・`?` のどれか、行の最後に）")
        if not words:
            raise KitError(f"{no} 行目：印だけの行")
        out.append((no, indented, words, mark))
    return out


@dataclass
class Sheet:
    kit: Line | None = None
    mode: Line | None = None
    hp: Line | None = None
    blocks: list[Block] = field(default_factory=list)


def parse(text: str) -> Sheet:
    sheet = Sheet()
    current: Block | None = None
    for no, indented, words, mark in read_lines(text):
        line = Line(no, words, mark)
        if indented:
            if current is None:
                raise KitError(f"{no} 行目：字下げした行の上に見出しが無い")
            current.lines.append(line)
            continue
        current = None
        head = words[0]
        if head == "kit":
            if sheet.kit or len(words) != 2:
                raise KitError(f"{no} 行目：`kit <name>` は 1 回だけ")
            sheet.kit = line
        elif head == "for":
            if sheet.mode or len(words) != 2 or words[1] not in ("play", "run"):
                raise KitError(f"{no} 行目：`for play` か `for run` を 1 回だけ")
            sheet.mode = line
        elif head == "hp":
            if sheet.hp or len(words) not in (2, 3):
                raise KitError(f"{no} 行目：`hp <hp> [unit=<scale>]` を 1 回だけ")
            sheet.hp = line
        elif head in MOVE_ALIASES:
            if len(words) != 1:
                raise KitError(f"{no} 行目：技の見出しは名前だけ（`{head}`）。中身は字下げして書く")
            name = MOVE_ALIASES[head]
            if any(b.kind == "move" and b.name == name for b in sheet.blocks):
                raise KitError(f"{no} 行目：`{name}` の見出しが 2 回ある")
            current = Block(line, "move", name)
            sheet.blocks.append(current)
        elif head in HEADER_ALIASES:
            kind = HEADER_ALIASES[head]
            if len(words) != 1 or any(b.kind == kind for b in sheet.blocks):
                raise KitError(f"{no} 行目：`{head}` の見出しは 1 回だけ、名前だけ")
            current = Block(line, kind, kind)
            sheet.blocks.append(current)
        else:
            raise KitError(f"{no} 行目：知らない見出し `{head}`")
    return sheet


# ---------------------------------------------------------------------------
# Values with units.


def length(value: str, vocab: dict, where: str) -> str:
    """A length a tick in the original's units: a number, or `<n>mbon` in
    MBON's (times saikai's length scale, 20/3 by default)."""
    if value == "-":
        return value
    num, den = vocab["length_scale"]
    try:
        if value.endswith("mbon"):
            v = Fraction(value[:-4]) * num / den
        else:
            v = Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise KitError(f"{where}：長さ `{value}` が読めない") from None
    if v < 0:
        raise KitError(f"{where}：長さは 0 以上")
    micro = round(v * 1_000_000)
    whole, frac = divmod(micro, 1_000_000)
    return str(whole) if frac == 0 else f"{whole}.{str(frac).rjust(6, '0').rstrip('0')}"


def carry(words: list[str], vocab: dict, where: str) -> str:
    """`move`, `own`, `stop`, `stop:<start>/<ground>/<air>`, then `cap=<h>/<v>`."""
    if not words or not CARRY_RE.match(words[0]):
        raise KitError(f"{where}：慣性は `move`・`own`・`stop`・`stop:<initial>/<ground>/<air>`")
    text = words[0]
    if text.startswith("stop:") and any(int(p) > 100 for p in text[5:].split("/")):
        raise KitError(f"{where}：慣性の率は 0〜100")
    rest = words[1:]
    if rest:
        if len(rest) != 1 or not rest[0].startswith("cap=") or not text.startswith("stop"):
            raise KitError(f"{where}：`cap=<horizontal>/<vertical>` は止まる武装（stop）にだけ 1 つ")
        parts = rest[0][4:].split("/")
        if len(parts) != 2:
            raise KitError(f"{where}：`cap=<horizontal>/<vertical>`")
        if text == "stop":
            text = "stop:50/92/94"
        text += " cap=" + "/".join(length(p, vocab, where) for p in parts)
    elif text == "stop":
        text = "stop:50/92/94"
    return text


def split_table(text: str) -> list[tuple[str, str]]:
    rows = []
    for item in text.split(";"):
        key, value = item.split("=", 1)
        rows.append((key, value))
    return rows


# ---------------------------------------------------------------------------
# Compiling.


@dataclass
class Move:
    name: str
    block: Block | None
    perf: tuple[str | None, str | None] | None = None
    perf_line: Line | None = None

    def perfs(self) -> list[str]:
        if not self.perf:
            return []
        out = []
        for p in self.perf:
            if p and p not in out:
                out.append(p)
        return out


class Compiler:
    def __init__(self, sheet: Sheet, vocab: dict):
        self.sheet = sheet
        self.v = vocab
        self.env: dict[str, str] = {}
        self.files: dict[str, str] = {}
        self.notes: list[str] = []
        self.warnings: list[str] = []
        self.prov: list[Provenance] = []
        self.mode = sheet.mode.words[1] if sheet.mode else "play"
        self.kit = sheet.kit.words[1] if sheet.kit else None
        if self.kit is not None and self.kit not in vocab["bases"]:
            raise KitError(f"{sheet.kit.where()}：キット `{self.kit}` は無い（{', '.join(vocab['bases'])}）")
        self.base = vocab["bases"][self.kit] if self.kit else vocab["bases"]["rena"]
        self.moves: dict[str, Move] = {}
        self.system: dict[str, tuple[Line, list[str]]] = {}
        self.raw: dict[str, tuple[Line, str]] = {}

    # -- bookkeeping --------------------------------------------------------

    def note_line(self, var: str, what: str, line: Line) -> None:
        if self.mode == "run" and line.mark is None:
            raise KitError(
                f"{line.where()}：`for run` では値に出どころの印が要る"
                "（ユーザーの決定は `!J<id>`、提案は `?U<id>` か `?`）"
            )
        self.prov.append(Provenance(var, what, line.mark, line.no))

    # -- the sheet's parts --------------------------------------------------

    def collect(self) -> None:
        for block in self.sheet.blocks:
            if block.kind == "move":
                self.collect_move(block)
            elif block.kind == "system":
                for line in block.lines:
                    layer = line.words[0]
                    if layer not in self.v["layers"]:
                        raise KitError(f"{line.where()}：知らない層 `{layer}`")
                    if layer == "kit":
                        raise KitError(f"{line.where()}：キットは `kit <name>` の見出しで書く")
                    if layer in self.system:
                        raise KitError(f"{line.where()}：層 `{layer}` を 2 回書いている")
                    if line.words[1:] == ["off"]:
                        continue
                    self.system[layer] = (line, line.words[1:])
            elif block.kind == "raw":
                for line in block.lines:
                    if len(line.words) < 2 or not line.words[0].startswith("SAIKAI_"):
                        raise KitError(f"{line.where()}：`raw` の行は `SAIKAI_<name> <value>`")
                    self.raw[line.words[0]] = (line, " ".join(line.words[1:]))

    def collect_move(self, block: Block) -> None:
        move = Move(block.name, block)
        self.moves[block.name] = move
        seen = set()
        for line in block.lines:
            prop = PROP_ALIASES.get(line.words[0])
            if prop is None:
                raise KitError(f"{line.where()}：`{block.name}` の知らない項目 `{line.words[0]}`")
            if prop in seen:
                raise KitError(f"{line.where()}：`{block.name}` の `{prop}` を 2 回書いている")
            seen.add(prop)
            if prop == "perf":
                if block.name in WEAPON_ROWS:
                    raise KitError(
                        f"{line.where()}：`{block.name}` はキットの外（原作の controller が出す）。"
                        "演目を結べるのは sub_shot・special_shot・special_melee・charge_shot・down_melee だけ"
                    )
                move.perf = self.read_perf(line)
                move.perf_line = line

    def read_perf(self, line: Line) -> tuple[str | None, str | None]:
        words = line.words[1:]
        if len(words) == 1:
            ground = air = words[0]
        elif len(words) == 3 and words[1] == "/":
            ground, air = words[0], words[2]
        else:
            raise KitError(f"{line.where()}：`perf <ground> [/ <air>]`（片側だけなら `-`）")
        ground = None if ground == "-" else ground
        air = None if air == "-" else air
        if ground is None and air is None:
            raise KitError(f"{line.where()}：地上にも空中にも演目が無い技は書けない（KitDef の NoPerformance）")
        for p in (ground, air):
            if p is not None:
                self.check_perf(p, line)
        return (ground, air)

    def check_perf(self, name: str, line: Line) -> None:
        perf = self.v["perfs"].get(name)
        if perf is None:
            raise KitError(f"{line.where()}：演目 `{name}` は演目表に無い（起動時に unknown_performance で断られる）")
        base = self.base["class"]
        if perf["class"] != base and base not in perf.get("borrowed_onto", []):
            raise KitError(
                f"{line.where()}：`{name}`（{perf['class']}）を {self.base['name']}（{base}）へ借りた実測が無い"
                "（起動時に unmeasured_borrow で断られる）"
            )

    # -- the kit ------------------------------------------------------------

    def compile_kit(self) -> None:
        if self.kit is None:
            bound = [m for m in self.moves if m not in WEAPON_ROWS and self.moves[m].perf]
            if bound:
                raise KitError(f"{self.moves[bound[0]].perf_line.where()}：演目を結ぶには `kit <name>` が要る")
            return
        spec = self.v["kits"][self.kit]
        options = []
        for name in self.v["kit_moves"]:
            move = self.moves.get(name)
            perf = move.perf if move else None
            if name in spec["fixed"]:
                fixed = tuple(spec["fixed"][name])
                if perf is not None and perf != fixed:
                    raise self.needs_v1(move, f"`{name}` は今のキット `{self.kit}` では {fixed[0]} / {fixed[1]} に決まっている")
                if perf is None and move is not None:
                    self.notes.append(f"`{name}` の演目はキットの既定 {fixed[0]} / {fixed[1]}")
                if move and move.perf_line:
                    self.note_line("SAIKAI_KIT", f"{name} perf", move.perf_line)
                continue
            choices = spec["choices"].get(name)
            if choices is None:
                if perf is not None:
                    raise self.needs_v1(move, f"キット `{self.kit}` の `{name}` には、いまの SAIKAI_KIT で結べる演目が無い")
                continue
            if perf is None:
                continue
            key = perf[0] if perf[0] == perf[1] else f"{perf[0]}/{perf[1]}"
            if key not in choices:
                raise self.needs_v1(move, f"`{name}` の演目 `{key}` は SAIKAI_KIT の選択肢（{', '.join(choices)}）に無い")
            choice = choices[key]
            if choice != spec["defaults"].get(name):
                options.append(f"{name}={choice}")
            self.note_line("SAIKAI_KIT", f"{name} perf", move.perf_line)
        self.env["kit"] = " ".join([self.kit, *options])
        self.bound = self.kit_perfs()
        donors = sorted({self.v["perfs"][p]["class"] for m in self.bound.values() for p in m if p}
                        - {self.base["class"]})
        if len(donors) > self.v["max_donor_classes"]:
            raise KitError(
                f"借りる技のクラスが {len(donors)} つ（{', '.join(donors)}）。1 戦闘に 2 つまで"
                "（起動時に too_many_donors で断られる）"
            )

    def needs_v1(self, move: Move | None, why: str) -> KitError:
        where = move.perf_line.where() if move and move.perf_line else self.sheet.kit.where()
        return KitError(
            f"{where}：{why}。v0 は今の SAIKAI_KIT の文字列にしか訳せない。"
            "この割り当てには saikai 側で SAIKAI_KIT=@<kit-file> を読む変更（README の v1）が要る"
        )

    def kit_perfs(self) -> dict[str, tuple[str | None, str | None]]:
        """The kit's moves as the runtime will build them: the sheet's perf or
        the kit's fixed one; the down melee only when bound."""
        spec = self.v["kits"][self.kit]
        out = {}
        for name in self.v["kit_moves"]:
            move = self.moves.get(name)
            if move and move.perf:
                out[name] = move.perf
            elif name in spec["fixed"]:
                out[name] = tuple(spec["fixed"][name])
            elif name == "special_melee" and self.kit == "rena":
                out[name] = ("iron.slide_melee", "iron.slide_melee")
        return out

    # -- layers -------------------------------------------------------------

    def layer_on(self, layer: str) -> bool:
        return layer in self.system

    def options(self, layer: str) -> dict[str, str]:
        line, words = self.system[layer]
        form = self.v["layers"][layer].get("form")
        out: dict[str, str] = {}
        if form in ("free", "table", "hp"):
            return out
        for w in words:
            if form == "comma" and w == "observe":
                out["observe"] = ""
                continue
            if "=" not in w:
                raise KitError(f"{line.where()}：`{layer}` の項目 `{w}` は `<key>=<value>` で書く")
            key, value = w.split("=", 1)
            allowed = self.v["layers"][layer]["keys"]
            ok = key in allowed or any(a.endswith("*") and key.startswith(a[:-1]) for a in allowed)
            if not ok:
                raise KitError(f"{line.where()}：`{layer}` に鍵 `{key}` は無い（{', '.join(allowed) or 'なし'}）")
            out[key] = value
        return out

    def check_support(self) -> None:
        free = set(self.v["slot_free_layers"])
        for layer, (line, _) in self.system.items():
            if layer in free or layer in self.base["layers"]:
                continue
            if layer == "step" and self.kit == "mion":
                raise KitError(
                    f"{line.where()}：水鉄砲にはステップがまだ入らない（J77、unsupported_class）。"
                    "loco を書けば、loco を運ぶための SAIKAI_STEP=on は kitc が立てる"
                )
            raise KitError(
                f"{line.where()}：層 `{layer}` は {self.base['name']} にまだ入らない"
                "（J77：対応するまで断る。起動時に installed=0 reason=unsupported_class）"
            )
        if self.kit == "mion" and "homing" in self.system:
            self.warnings.append("homing：水鉄砲の弾は誘導しない（効くのは相手のステップでの誘導切りだけ）")

    def resolve_needs(self) -> None:
        if self.kit is not None and "commands" not in self.system:
            self.env["commands"] = "on"
            self.notes.append("SAIKAI_COMMANDS=on を足した（キットは同時押しの層に載る）")
        for layer in list(self.system):
            for need in self.v["layers"][layer].get("needs", []):
                if need == "kit":
                    if self.kit is None:
                        raise KitError(f"{self.system[layer][0].where()}：`{layer}` はキットが要る")
                elif need == "commands":
                    if "commands" not in self.system and "commands" not in self.env:
                        self.env["commands"] = "on"
                        self.notes.append(f"SAIKAI_COMMANDS=on を足した（`{layer}` が要る）")
                elif need == "step" and "step" not in self.system:
                    if self.kit == "mion":
                        self.env["step"] = "on"
                        self.notes.append(
                            "SAIKAI_STEP=on を足した：水鉄砲ではステップ自体は unsupported_class で入らず、"
                            "フックが loco だけを運ぶ（saikai F188、docs/loco.md「水鉄砲」）"
                        )
                    else:
                        raise KitError(f"{self.system[layer][0].where()}：`{layer}` は `step` が要る（needs_step）")
                elif need not in self.system:
                    raise KitError(f"{self.system[layer][0].where()}：`{layer}` は `{need}` が要る")

    def emit_layers(self) -> None:
        for layer, (line, words) in self.system.items():
            var = "SAIKAI_" + layer.upper()
            form = self.v["layers"][layer].get("form")
            if form == "table":
                continue  # inertia and boost_cost: compile_tables
            if form == "hp":
                self.emit_hp(line, words)
                continue
            if form == "free":
                self.env[layer] = " ".join(words) if words else "on"
                self.note_line(var, "on", line)
                continue
            opts = self.options(layer)
            if form == "comma":
                items = [k if k == "observe" else f"{k}={v}" for k, v in opts.items()]
                self.env[layer] = ",".join(items) if items else "on"
            else:
                self.env[layer] = " ".join(["on", *(f"{k}={v}" for k, v in opts.items())])
            self.note_line(var, " ".join(words) or "on", line)

    def emit_hp(self, line: Line, words: list[str]) -> None:
        self.env["hp"] = "on " + " ".join(words) if words else "on"
        self.note_line("SAIKAI_HP", " ".join(words) or "on", line)

    # -- the move-major properties, transposed into layers -------------------

    def move_lines(self, prop: str):
        for name, move in self.moves.items():
            for line in move.block.lines if move.block else []:
                if PROP_ALIASES[line.words[0]] == prop:
                    yield name, move, line

    def require(self, layer: str, line: Line, prop: str) -> bool:
        if layer in self.system:
            return True
        self.warnings.append(f"{line.where()}：`{prop}` を書いたが system に `{layer}` が無いので効かない")
        return False

    def set_key(self, layer: str, key: str, value: str, line: Line) -> None:
        """Adds `key=value` to a layer's `on ...` text; refuses a key the system
        line already gives."""
        opts = self.options(layer)
        if key in opts:
            raise KitError(
                f"{line.where()}：`{layer}` の `{key}` を技の中と system の両方で書いている"
                f"（system は {self.system[layer][0].where()}）"
            )
        self.env[layer] += f" {key}={value}"

    def compile_ammo(self) -> None:
        for name, _, line in self.move_lines("ammo"):
            if name not in self.v["ammo_rows"]:
                raise KitError(f"{line.where()}：弾倉を持てるのは {', '.join(self.v['ammo_rows'])}（`{name}` は無い）")
            value = " ".join(line.words[1:])
            if not MAG_RE.match(value):
                raise KitError(f"{line.where()}：弾倉は `<constant|depleted|never|manual>/<capacity>/<reload>[/<burst_reload>]…` か `none`")
            if name == "main" and ("/hold" in value or value.startswith("manual")):
                raise KitError(f"{line.where()}：メインの弾倉に hold・manual は使えない")
            if self.require("ammo", line, "ammo"):
                self.set_key("ammo", name, value, line)
                self.note_line("SAIKAI_AMMO", f"{name}={value}", line)

    def compile_cancel(self) -> None:
        to_all = list(self.v["cancel_to"])
        member = {c: True for c in to_all}
        dry = {c: False for c in to_all}
        touched = False
        for name, _, line in self.move_lines("cancel"):
            words = line.words[1:]
            if name not in to_all:
                raise KitError(f"{line.where()}：メインを打ち切れるのは {', '.join(to_all)}")
            if words == ["main"]:
                member[name], dry[name] = True, False
            elif words == ["main", "dry"]:
                member[name], dry[name] = True, True
            elif words == ["none"]:
                member[name], dry[name] = False, False
            else:
                raise KitError(f"{line.where()}：`cancel main`・`cancel main dry`・`cancel none` のどれか")
            if self.require("cancel", line, "cancel"):
                touched = True
                self.note_line("SAIKAI_CANCEL", f"{name}: {' '.join(words)}", line)
        for name, _, line in self.move_lines("shots"):
            if name != "main":
                raise KitError(f"{line.where()}：`shots` は `main` の見出しにだけ書く（キャンセルできるメインの演目）")
            shots = line.words[1:]
            for s in shots:
                if s not in self.base["mains"]:
                    raise KitError(f"{line.where()}：`{s}` は {self.base['name']} のメインの演目ではない（{', '.join(self.base['mains'])}）")
            if self.require("cancel", line, "shots") and shots != self.base["mains"]:
                self.set_key("cancel", "from", ",".join(shots), line)
                self.note_line("SAIKAI_CANCEL", "from=" + ",".join(shots), line)
        if not touched:
            return
        to = [c for c in to_all if member[c]]
        if not to:
            raise KitError("キャンセルの行き先が 1 つも無い（SAIKAI_CANCEL は to=none を取らない。system から cancel を外す）")
        if to != to_all:
            self.set_key("cancel", "to", ",".join(to), self.system["cancel"][0])
        excepts = [c for c in to_all if member[c] and dry[c]]
        if excepts:
            self.set_key("cancel", "except", ",".join(excepts), self.system["cancel"][0])

    def compile_air(self) -> None:
        keeps = []
        for name, move, line in self.move_lines("air"):
            if line.words[1:] != ["keep"]:
                raise KitError(f"{line.where()}：`air keep`（空中では空中の演目を残す）")
            air = self.bound.get(name, (None, None))[1] if self.kit else None
            if air is None:
                raise KitError(f"{line.where()}：`{name}` に空中の演目が無い")
            if self.require("air", line, "air keep"):
                keeps.append(air)
                self.note_line("SAIKAI_AIR", f"keep {air}", line)
        if keeps:
            self.set_key("air", "keep", ",".join(keeps), self.system["air"][0])
        if "air" in self.system and self.kit == "rena":
            written = self.options("air").get("keep", "")
            kept = set(keeps) | set(filter(None, written.split(","))) | {"axe.air_shot"}
            for name, (ground, air) in self.bound.items():
                if air and ground and air != ground and air not in kept:
                    self.notes.append(
                        f"air：`{name}` は空中でも地上の {ground} を演じる（空中の {air} は残していない。残すなら `air keep`）"
                    )

    def compile_rainbow(self) -> None:
        chosen = list(self.v["step_rainbow_air_default"])
        touched = None
        for name, _, line in self.move_lines("rainbow"):
            words = line.words[1:]
            if words not in (["air"], ["ground"]):
                raise KitError(f"{line.where()}：`rainbow air`（この技からの虹ステを空中扱い）か `rainbow ground`")
            if not self.kit or name not in self.bound:
                raise KitError(f"{line.where()}：`rainbow` はキットの技にだけ書ける")
            for p in filter(None, self.bound[name]):
                if p not in self.v["perf_all"]:
                    raise KitError(f"{line.where()}：`{p}` は rainbow_air= に書けない（perf::ALL の 24 個だけ）")
                if words == ["air"] and p not in chosen:
                    chosen.append(p)
                if words == ["ground"] and p in chosen:
                    chosen.remove(p)
            if self.require("step", line, "rainbow"):
                touched = line
                self.note_line("SAIKAI_STEP", f"{name}: rainbow {words[0]}", line)
        if touched and chosen != self.v["step_rainbow_air_default"]:
            self.set_key("step", "rainbow_air", "+".join(chosen) if chosen else "none", touched)

    def compile_tables(self) -> None:
        # SAIKAI_INERTIA: a written table starts from `default=stop` alone, so
        # kitc writes the whole `on` table with the sheet's rows over it.
        rows = []
        for name, _, line in self.move_lines("inertia"):
            text = carry(line.words[1:], self.v, line.where())
            if self.require("inertia", line, "inertia"):
                rows.append((name, text))
                self.note_line("SAIKAI_INERTIA", f"{name}={text}", line)
        if "inertia" in self.system:
            line, words = self.system["inertia"]
            table = dict(split_table(self.v["inertia_on"]))
            for name, text in rows:
                table[name] = text
            out = ";".join(f"{k}={v}" for k, v in table.items())
            self.emit_table("inertia", line, words, "on" if not rows else out, out)
        # SAIKAI_BOOST_COST: a written table starts from the `on` table.
        rows = []
        for name, move, line in self.move_lines("boost"):
            spend = " ".join(line.words[1:])
            if not SPEND_RE.match(spend):
                raise KitError(f"{line.where()}：消費は `none`・`carry`・`whole:<F>`・`lunge:<F>`・`window:<F>x<n>`（`<initial>+` も可）")
            if name == "main":
                perfs = self.base["mains"]
            elif name == "melee":
                perfs = self.base["melees"]
            else:
                perfs = [p for p in self.bound.get(name, ()) if p] if self.kit else []
                if not perfs:
                    raise KitError(f"{line.where()}：`{name}` に演目が無い（キットに結ばれていない）")
            if self.require("boost_cost", line, "boost"):
                rows += [(p, spend) for p in dict.fromkeys(perfs)]
                self.note_line("SAIKAI_BOOST_COST", f"{name}: {spend}", line)
        if "boost_cost" in self.system:
            line, words = self.system["boost_cost"]
            out = ";".join(f"{p}={s}" for p, s in rows)
            full = dict(split_table(self.v["boost_cost_on"]))
            full.update(rows)
            self.emit_table("boost_cost", line, words, out or "on",
                            ";".join(f"{k}={v}" for k, v in full.items()))

    def emit_table(self, layer: str, line: Line, words: list[str], value: str, whole: str) -> None:
        var = "SAIKAI_" + layer.upper()
        file = None
        for w in words:
            if w.startswith("file="):
                file = w[5:]
            else:
                raise KitError(f"{line.where()}：`{layer}` の system の行に書けるのは `file=<path>` だけ（行は技の中に書く）")
        if file:
            self.files[file] = "# kitc が書いた。直接直さず .kit を直して kitc をもう一度\n" + whole.replace(";", "\n") + "\n"
            self.env[layer] = "@" + file
            if layer == "boost_cost":
                self.notes.append(f"{var}=@{file}：戦闘の始めにだけ読む（戦闘中に直しても次の戦闘から）")
            else:
                self.notes.append(f"{var}=@{file}：戦闘中も 30 更新ごとに読み直す")
        else:
            self.env[layer] = value
        self.note_line(var, value if value == "on" else "table", line)

    # -- the whole ----------------------------------------------------------

    def compile(self) -> Result:
        self.collect()
        self.bound = {}
        self.compile_kit()
        self.check_support()
        self.resolve_needs()
        self.emit_layers()
        self.compile_ammo()
        self.compile_cancel()
        self.compile_air()
        self.compile_rainbow()
        self.compile_tables()
        if self.sheet.hp:
            if self.kit is None:
                raise KitError(f"{self.sheet.hp.where()}：`hp` はキットのキャラクターの耐久値。`kit` が要る")
            words = self.sheet.hp.words[1:]
            value = f"{self.base['character']}={words[0]}"
            if len(words) == 2:
                if not words[1].startswith("unit="):
                    raise KitError(f"{self.sheet.hp.where()}：`hp <hp> [unit=<scale>]`")
                value = f"{words[1]} {value}"
            if "hp" in self.system:
                self.env["hp"] += " " + value
            else:
                self.env["hp"] = "on " + value
            self.note_line("SAIKAI_HP", value, self.sheet.hp)
        for var, (line, value) in self.raw.items():
            key = var[len("SAIKAI_"):].lower()
            if key in self.env:
                raise KitError(f"{line.where()}：`{var}` は kitc も書く（raw で上書きしない）")
            self.env[key] = value
            self.note_line(var, "raw", line)
            self.warnings.append(f"{line.where()}：`{var}` は raw のまま（kitc は中身を検査していない）")
        order = {k: i for i, k in enumerate(ENV_ORDER)}
        env = {
            "SAIKAI_" + k.upper(): v
            for k, v in sorted(self.env.items(), key=lambda kv: (order.get(kv[0], 99), kv[0]))
        }
        return Result(env, self.files, self.notes, self.warnings, self.prov, self.mode, self.kit)


def compile_text(text: str, vocab: dict | None = None) -> Result:
    return Compiler(parse(text), vocab or load_vocab()).compile()


# ---------------------------------------------------------------------------
# Output.


def quote_inline(value: str) -> str:
    return f'"{value}"' if re.search(r"[\s;\"']", value) else value


def cmd_escape(value: str) -> str:
    """cmd's `set` takes the rest of the line; its operators need a caret."""
    return re.sub(r"([&|<>^])", r"^\1", value)


def render(result: Result, shell: str, clear: bool, vocab: dict) -> str:
    # A research knob left over in the shell changes the run silently
    # (SAIKAI_S0 replaces the kit's borrowed moves), so it is cleared too.
    known = ["SAIKAI_" + k.upper() for k in vocab["layers"]] + vocab["research_knobs"]
    lines = []
    if shell == "inline":
        return " ".join(f"{k}={quote_inline(v)}" for k, v in result.env.items())
    stale = [k for k in known if k not in result.env] if clear else []
    if shell == "cmd":
        lines += [f"set {k}=" for k in stale]
        lines += [f"set {k}={cmd_escape(v)}" for k, v in result.env.items()]
    elif shell == "ps":
        lines += [f"Remove-Item Env:{k} -ErrorAction SilentlyContinue" for k in stale]
        lines += [f"$env:{k} = '{v.replace(chr(39), chr(39) * 2)}'" for k, v in result.env.items()]
    elif shell == "sh":
        lines += [f"unset {k}" for k in stale]
        lines += [f"export {k}='{v}'" for k, v in result.env.items()]
    return "\n".join(lines)


def report(result: Result) -> str:
    out = [f"kit={result.kit or '-'} for={result.mode} hash={result.digest()} vars={len(result.env)}"]
    decided = [p for p in result.provenance if p.mark and p.mark.startswith("!")]
    proposed = [p for p in result.provenance if p.mark and p.mark.startswith("?")]
    unmarked = [p for p in result.provenance if not p.mark]
    out.append(f"出どころ：ユーザーの決定 {len(decided)}、提案 {len(proposed)}、印なし {len(unmarked)}")
    for p in sorted(result.provenance, key=lambda p: p.line):
        out.append(f"  {p.line:>3} 行目  {p.mark or '  -  ':<6} {p.var:<18} {p.what}")
    for n in result.notes:
        out.append("note: " + n)
    for w in result.warnings:
        out.append("warn: " + w)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="daybreak-saikai のキットの紙（.kit）を SAIKAI_* の設定に訳す試作")
    ap.add_argument("sheet", type=Path)
    ap.add_argument("--shell", choices=["cmd", "ps", "sh", "inline"], default="cmd")
    ap.add_argument("--no-clear", action="store_true", help="紙に無い SAIKAI_* を消す行を出さない")
    ap.add_argument("--report", action="store_true", help="出どころ・注記・警告を標準エラーへ")
    ap.add_argument("--files", type=Path, help="file= の表を書き出す先（既定は .kit と同じ場所）")
    args = ap.parse_args(argv)
    vocab = load_vocab()
    try:
        result = Compiler(parse(args.sheet.read_text(encoding="utf-8")), vocab).compile()
    except KitError as e:
        print(f"{args.sheet}: {e}", file=sys.stderr)
        return 1
    base = (args.files or args.sheet.parent).resolve()
    for name, text in result.files.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        # The game reads the file from its own working directory: give it
        # the whole path.
        for var, value in result.env.items():
            if value == "@" + name:
                result.env[var] = "@" + str(path)
    print(render(result, args.shell, not args.no_clear, vocab))
    if args.report:
        print(report(result), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
