# saikai-kit-dsl：キットを人が調整するための「キットの紙」

[daybreak-saikai](https://gitlab.com/hidebu-reiwa/daybreak-saikai)（ひぐらしデイブレイクの非公式 MOD。以下 saikai）のキットを、人が技ごとに書いて調整するための小さな言語（`.kit`）と、その試作コンパイラ `kitc.py`。

調べたのは saikai の main `abe253c`（2026-09-26）。saikai 側のコードは一行も変えていない。

## 概要

- `.kit` は、キットを「技ごと」に書く紙。たとえばサブなら、演目・慣性・弾倉・メインからのキャンセル・ブースト消費を一か所にまとめる。
- `kitc.py` はその紙を、今の saikai が読む `SAIKAI_*` の環境変数へ転置する。saikai 側の変更は要らない（これを v0 と呼ぶ）。
- 訳すときに、次のことを検査する。
  - 名前が語彙にあるか
  - ベースのクラスで使える層か
  - 借用に実測があるか、借りるクラスが上限の 2 を超えないか
  - 層どうしの隠れた依存
  - 表の上書きの規則
  - 値の出どころ（ユーザーの決定か提案か）
- ユーザーがいま手で遊んでいる設定（環境変数 20 個）は、32 行の紙で書けた。訳した結果は記録と完全に一致した。
- 訳した値は、saikai-rules の本物のパーサーにすべて受理された。

レナのキットの今の作りを追った記録は [notes/rena-kit-current.md](notes/rena-kit-current.md)、技と弾を個別に調整する見通しは [notes/per-move-and-shot-tuning.md](notes/per-move-and-shot-tuning.md) にある。

## 動機

### 事実

- **キットそのものは、コマンドと演目の対応しか持っていない。**
  - キット（`saikai-rules::kit::KitDef`）が持つのは、コマンド → 技 → 地上と空中の演目名、という対応だけ。
  - 技の性質は、8 つの層の設定に散らばっている：慣性（`SAIKAI_INERTIA`）、ブースト消費（`SAIKAI_BOOST_COST`）、弾倉（`SAIKAI_AMMO`）、キャンセル（`SAIKAI_CANCEL`）、CS が切る技（`SAIKAI_CHARGE`）、空中の演目（`SAIKAI_AIR`）、虹ステ（`SAIKAI_STEP`）、耐久値（`SAIKAI_HP`）。
  - 各層の鍵は、演目名かコマンド名。
- **遊ぶときの設定は、環境変数 20 個を並べたもの。** 出典は `experiments/down-melee-axe.md`。
- **層ごとに文法が違う。** saikai-rules の本物のパーサーで確かめた（検証器 `oracle/`）。
  - 区切り：`SAIKAI_STEP="on,shot=keep"` は通るが、`SAIKAI_AIR="on,blend=20"` と `SAIKAI_CHARGE="on,full=100"` は `NotOn` で弾かれる。
  - 表の上書き：`SAIKAI_INERTIA="sub_shot=stop:60/80/85"` と書くと、`on` の表の 9 行（移動撃ちの `main=move`、格闘の `melee=own` など）が消えて、`default=stop:50/92/94;sub_shot=…` だけになる。一方 `SAIKAI_BOOST_COST="nata.shot=whole:10"` は、`on` の表に行を足す。同じ「表を書く」操作なのに、上書きの規則が逆になっている。
  - 貼り戻し：`SAIKAI_UKEMI` の run 記録用の正規形 `on wait=48 scale=20/3 …` を設定に貼り戻すと、`Unknown("scale=20/3")` で弾かれる（`ukemi.rs` の `to_text` が、`parse` の知らない鍵を書いている）。
- **隠れた依存がある。** 水鉄砲（魅音）で LOCO を使うには `SAIKAI_STEP=on` が要る。ステップ自体は水鉄砲では `unsupported_class` で入らないが、立てないと LOCO が `needs_step` で断られる（`loco.rs` の `install`、saikai F188）。
- **設計の文書で、宣言的なデータ形式は未決。** キットと技表を宣言的なデータへ出すかは U7 で、「目安は 2 キャラ目のキット」とある。その 2 キャラ目（魅音、J75）が今始まっている。一方、スクリプト VM（Lua など）は不採用と決まっている（`docs/tech-stack.md`）。

### 推測（示唆）

- **人が触る単位と、設定が並ぶ単位がずれている。** 人は「サブをもう少し滑らせたい」と技の単位で考えるが、設定は層の単位で並んでいる。根拠は、上の 8 か所の鍵がどれも演目名かコマンド名で、一つの技の調整が複数の環境変数に割れること。
- **今が形式を決めるのにちょうどよい時期。** 根拠：U7 の目安（2 キャラ目）に達した。層を水鉄砲へ広げる段 2 も進んでいて、手で遊んで値を決める依頼（J56 のカメラ、U31 の慣性、U41 の BD の見た目など）が増えている。

## 手法

1. saikai をクローンし、レナのキットを入力から原作の演技まで読んだ（[notes/rena-kit-current.md](notes/rena-kit-current.md)）。
2. サブエージェントに、`SAIKAI_*` 24 個の文法（鍵・区切り・`@file`・正規形・対応クラス）を洗い出させた。要になる主張は自分で読み直した。
3. saikai-rules が Linux でも build できることを確かめた。そのうえで、文字列を本物のパーサーに通して正規形を返す小さな Rust の検証器（`oracle/`）を作った。`on` の表と各層の既定値は、この検証器で出力して `vocab.json` に写した。
4. 紙の言語を決め、Python の標準ライブラリだけで `kitc.py` を書いた。saikai の `tools/` と同じ流儀にするため。
5. テスト 25 本を書いた。うち 1 本は、全例の出力を検証器に通すもの（`KITC_ORACLE=1` のときだけ動く）。

## 言語（`.kit`）

```text
kit rena                                  # キット（ベースのクラスも決まる：rena＝鉈 0:0、mion＝水鉄砲 1:1）
for play                                  # play＝手で遊ぶ／run＝証拠の run（印の無い値を拒む）
hp 12000                          ?       # このキャラクターの耐久値（SAIKAI_HP の rena=）

メイン                                    # 見出し（字下げなし）。main・melee・sub_shot… か、メイン・格闘・サブ・特射・特格・射CS・下格
  inertia  move                           # 項目（字下げ）
  ammo     constant/6/180/120
  shots    nata.shot nata.lever_shot nata.air_shot

サブ
  inertia  stop:60/80/85 cap=-/4.0mbon    ?U60     # 行の最後に出どころの印
  ammo     depleted/3/240/180             ?U43
  cancel   main                                    # メインを打ち切れる（main dry：空撃ちからも／none：打ち切らない）
  air      keep                                    # SAIKAI_AIR の下でも空中の演目を残す
  boost    whole:30

下格
  perf     axe.shot / axe.air_shot        !J50     # 地上 / 空中（片側だけなら -）
  rainbow  air                            !J61     # この技からの虹ステは空中扱い

system                                    # 層（書けば on。鍵は各層のものだけ）
  step     shot=keep
  loco     parts=bd air=on blend=7
  inertia  file=rena.inertia.txt          # 表をファイルに出す（戦闘中も 30 更新ごとに読み直される）
  cancel
  ammo

raw                                       # 逃げ道：kitc が検査しない SAIKAI_* をそのまま
  SAIKAI_TRACE_MOVE 0:280-2599
```

| 項目 | 書ける見出し | 行き先 |
|---|---|---|
| `perf <地上> [/ <空中>]` | サブ・特射・特格・射CS・下格 | `SAIKAI_KIT`（v0 は今の選択肢に訳せるものだけ） |
| `inertia <move\|own\|stop[:a/b/c]> [cap=h/v]` | どれも | `SAIKAI_INERTIA` の、その技の行（`on` の表の上に重ねる） |
| `ammo <弾倉>` | メイン・サブ・特射・特格 | `SAIKAI_AMMO` の、そのコマンドの鍵 |
| `cancel main\|main dry\|none` | サブ・特射・特格・下格 | `SAIKAI_CANCEL` の `to=`・`except=` |
| `shots <演目>…` | メイン | `SAIKAI_CANCEL` の `from=` |
| `air keep` | キットの技 | `SAIKAI_AIR` の `keep=` |
| `rainbow air\|ground` | キットの技 | `SAIKAI_STEP` の `rainbow_air=` |
| `boost <消費>` | どれも（メイン・格闘は、ベースの演目すべて） | `SAIKAI_BOOST_COST` の、その技の演目の行 |

値の書き方は、今の層の文法をそのまま使う（`stop:60/80/85`、`depleted/3/240/180`、`whole:30`）。新しい記法は 2 つだけ足した。

- **出どころの印**：`!J<n>` はユーザーの決定、`?U<n>` と `?` は提案。
- **長さの単位 `mbon`**：MBON の長さで書くと、saikai の尺度 20/3 を掛けて原作の長さにする（`4.0mbon` → `26.666667`）。

変数、条件、繰り返しは持たない。有限の表へ訳すだけなので、スクリプト VM を採らないという saikai の決定と矛盾しない。

## 結果

### 事実

| 確かめたこと | 結果 | 証拠 |
|---|---|---|
| 遊びの設定（20 個）を紙で書けるか | 32 行の紙（見出しと項目の行は 25）で書け、訳した結果が記録と一致した | `test_the_play_sheet_is_the_recorded_play_setting` |
| 訳した値を saikai が受け付けるか | 全例のどの値も saikai-rules の本物のパーサーが `ok` を返した（saikai-rules にパーサーがある 16 層。COMBO・LOCK・CAMERA・HP は runtime 側で、確かめられていない） | `oracle/`、`test_every_example_parses_with_saikai_rules` |
| 慣性の行を足しても `on` の表が消えないか | `sub_shot` だけ書いても `main=move`・`melee=own`・`nata.ex=own` が残る | `test_an_inertia_row_goes_over_the_on_table` |
| 起動する前に断れるか | 次の 9 種類を、行番号つきの日本語で拒んだ：知らない演目（`unknown_performance`）、実測の無い借用（`unmeasured_borrow`）、借りるクラスの上限（`too_many_donors`）、水鉄砲にまだ入らない層（J77・`unsupported_class`）、鉈の `needs_step`、層に無い鍵、同じ鍵を技と system の両方で書く、`to=none`、`for run` での印の無い値 | `Refusals` の 13 本 |
| 隠れた依存を引き受けられるか | 水鉄砲の紙に `loco` を書くと、`SAIKAI_STEP=on` を足して理由（F188）を注記した | `test_the_water_guns_loco_gets_the_steps_hook` |
| 人が見落としやすい挙動を出せるか | `SAIKAI_AIR` の下で、空中の演目が演じられない技を注記した（今の遊びの設定では、サブ・特射・射CS の 3 つが空中でも地上の演目を演じる） | `test_air_says_which_air_performances_are_not_played` |

ついでに分かったこと：

- `SAIKAI_UKEMI` の正規形は、そのまま貼り戻せない（上の「動機」）。
- `saikai-runtime` は Linux では build できない。kakera-runtime が `windows`・`windows_sys` を要るため。`docs/tech-stack.md` で「未確認」とされていた点が、確かめられた。saikai-rules は Linux で build できた。

### 推測（示唆）

- **この言語の価値は、構文より「転置」と「検査」にある。** 根拠：値の記法は既存のままなのに、紙の側で直ったことが三つある。一つの技の調整が一か所に集まったこと。INERTIA と BOOST_COST の上書きの規則が逆なのを、利用者が知らなくてよくなったこと。起動しないと分からなかった拒否（`installed=0 …`）が、書いた時点で分かるようになったこと。
- **TOML や RON にしないほうがよい。** 根拠は三つ。
  - この紙で重いのは、技ごとの項目と、行ごとの出どころの印。TOML では `[moves.sub_shot] inertia = { value = "stop:…", mark = "U60" }` のような入れ子になり、読み書きの手間が増える。
  - 検査は、形式が何であれ `kitc` 側に要る。形式を汎用にしても、手に入るのはパーサーだけ。
  - 行ごとの文法なので、パーサーは 100 行ほどで済む。
  - ただし、エディタの補助（補完・色分け）が無いのは不利。語彙が `vocab.json` にあるので、足すのは難しくない。
- **印は、saikai の台帳の規律を書き方に落としたもの。** 根拠：saikai は、提案（U）を決定（J）へ黙って昇格させないことを最重要の規則にしている（AGENTS.md、design-baseline.md）。紙の行に印があれば、`for run` で「どの値が決まっていたか」を run 記録に機械的に残せる（`--report` の一覧と `hash=`）。

## 使い方

```sh
python3 kitc.py examples/rena-play.kit --shell cmd --report > saikai-env.cmd   # Windows の cmd
python3 kitc.py examples/rena-play.kit --shell ps                              # PowerShell
python3 kitc.py examples/rena-play.kit --shell inline                          # 実験記録に貼る形
python3 -m unittest discover -s tests -v                                       # テスト（検証器は飛ばす）
KITC_ORACLE=1 python3 -m unittest discover -s tests -v                         # 検証器つき（cargo と Rust 1.97.1、saikai を .saikai に clone する）
```

- `--shell cmd`・`ps`・`sh` は、紙に無い `SAIKAI_*` を消す行も出す（消さないなら `--no-clear`）。前に使った研究用の `SAIKAI_S0` が残っていると、キットの借用が黙って置き換わるから。
- `system` の `inertia file=<パス>` は表をファイルに書き、`@<絶対パス>` を渡す。戦闘中に紙を直して `kitc` を再実行すれば、30 更新以内に効く（saikai の `SAIKAI_INERTIA=@file` の読み直し）。`boost_cost` のファイルは戦闘の始めにしか読まれない。

## v1 以降（提案。saikai 側の判断が要る）

| 段 | saikai 側の変更 | 紙でできるようになること |
|---|---|---|
| v0（この試作） | なし | 今の選択肢の中でキットを選ぶことと、技ごとの性質の調整 |
| v1 | `SAIKAI_KIT` に、演目名だけで書いたキットの行を読む道を足す。例：`custom base=rena sub_shot=nata.backstep_shot/nata.air_shot special_melee=iron.slide_melee …`。rules で `KitDef` を作り、名前は `perf::named` で引く。起動時の検査は今のもの（`unknown_performance`・`unmeasured_borrow`・`too_many_donors`）を使う。あわせて `weapon::slot_map(Option<&ProvisionalKit>)` を `&KitDef` を受け取る形にする | どの演目をどのコマンドに結ぶかを、ビルドし直さずに変える。魅音のキットを紙で組む |
| v2 | 段 3 の controller（`docs/kit-model.md`）で、`MoveDef` に費用・キャンセル・フレームを持たせる | 紙の技の見出しが、そのまま `MoveDef` の行になる |

- v1 で `SAIKAI_KIT` にファイルではなく一行の文字列を渡すのは、`saikai-rules` に入出力を持ち込まないため（純ロジック・`#![forbid(unsafe_code)]`）。正規形は run 記録にそのまま残る。
- v2 の根拠：`docs/kit-model.md` の型の見本が `MoveDef { perf, cancels, cost, availability, frames }` で、技ごとにまとめる紙の形と同じ向きを向いている。

## 結論

- 人が使うキットの DSL は作れる。しかも v0 は、saikai を変えずに今日から使える。
- 効くのは新しい構文ではない。技ごとに書いたものを層ごとの設定へ転置すること、起動前に拒否を前倒しすること、出どころの印の三つよ。
- U7（宣言的な形式を採るか）への材料としては、「TOML ではなく、検査つきの行ごとの紙」を推したい。
- 次に確かめるべきことは三つ。
  - 実機：紙から作った設定で遊び、run 記録の `saikai_*_install` の行が、紙の報告と一致するか。
  - v1 の小さな変更を saikai に提案するかどうか（ユーザーの判断）。
  - 語彙（`vocab.json`）の手写しをやめて、saikai の側から書き出す口を作るか。

## 制限

- 実機では一度も動かしていない。「saikai-rules のパーサーが受理した」ことは、「ゲーム内でそう動いた」ことを意味しない。
- `vocab.json` は saikai `abe253c` の手写しで、saikai が進むと古くなる（検証器の `dump` で作り直せるのは、表と既定値の部分だけ）。
- COMBO・LOCK・CAMERA・HP・HUD・効果（`step_fx` など）の値は、今は素通しで、中身を検査していない。
- 値はどれも説明のための例で、キットの決定ではない。
