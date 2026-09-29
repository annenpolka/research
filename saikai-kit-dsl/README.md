# saikai-kit-dsl：人がキットの戦闘仕様を書くための言語

[daybreak-saikai](https://gitlab.com/hidebu-reiwa/daybreak-saikai) の技を、武装表のように読み書きするための研究。人が技ごとに指定した設定を、ゲームが読む実装層ごとの設定へ変換する。

## 現在の状態

**動作するv0の設定変換器と、未実装の統合設計を区別する。** `kitc.py` が受け付けるのは以下のv0構文と [examples/](examples/) の入力。`design/` の `format 1`、`bind`、`frames`、イベント相対キャンセル等を実装済みとは扱わない。

| 資料 | 目的 |
|---|---|
| [kitc.py](kitc.py)、[examples/](examples/) | 動作する設定変換器と入力例 |
| [範囲と責務](design/README.md) | 統合設計の基準。仕様と実装手続きの境界 |
| [記法とデータモデル](design/language.md) | 公開コマンド、技、資源、状態、派生、実験差分 |
| [時間・モーション](design/timing.md) | フレーム直指定、相対指定、時間変形 |
| [イベントと実行契約](design/events.md) | 観測、実行元、処理位相、保存・復元 |
| [実装計画と受入条件](design/implementation.md) | 対応能力、v0の制約、段階導入、今後の試験 |
| [旧ファイルの移行](MIGRATIONS.md) | 廃止した構文、移行診断、維持する互換契約 |
| [変更と検証の履歴](notes/change-history.md) | 各変更時点の記録。現在の仕様とは分離 |

## v0の文法と対応範囲

構文は英語ASCII表記。日本語の説明・コメント・ファイルパスはデータとして使える。引用符付き表示ラベルは統合設計の機能であり、v0の見出しには書けない。正規名は [コマンド一覧](design/language.md#21-主射撃と方向別格闘コマンド) を参照。互換用の `CS` だけは `charge_shot` の別名として受け付ける。

| コマンド | v0での扱い |
|---|---|
| `main_shot` | 主射撃の設定。弾倉・慣性はbackendの `main=` へ変換 |
| `sub_shot`、`special_shot`、`special_melee`、`charge_shot`、`down_melee` | 固定キットと語彙が対応する項目を変換 |
| `neutral_melee`、`up_melee`、`side_melee`、`boost_dash_melee` | 独立した見出しとして保持。非空の設定は `unsupported_command_split` で拒否 |

N格・前格・横格・下格・BD格は別の入力種別。未接続の4種を格闘全般へまとめて出力しない。空の見出しを読めることは、ゲーム内入力や性能調整に対応していることを意味しない。`down_melee` には既存の変換経路がある。

v0では `kit` がベースクラスと固定キットを選ぶ。原作の演目、借用先、依存関係、利用可能な設定キーは [vocab.json](vocab.json) の固定スナップショット（saikai `abe253c`）に従う。対象の選択肢にない演目割当は `unsupported_binding`。任意の新キットや方向別controllerを自動生成しない。

### 入力例

次はv0で使える記法の抜粋。性能値は調整例で、採用決定ではない。

```text
kit rena
for play

sub_shot
  inertia stop:60/80/85 ?
  ammo depleted/3/240/180 ?
  cancel main_shot

system
  inertia
  ammo
  cancel
```

`depleted/3/240/180` は撃ち切り・最大3発・通常240F・覚醒中180F。`system` は使用する層を有効にする。弾倉・慣性・ブースト消費等の値はv0では既存backendの書式を使う。名前付き値の統合設計とは別である。

公開コマンドとシリアライズ済みbackendの名前は別契約。`system` の `melee side=on`、`ammo main=...`、原作演目 `nata.front_melee` 等は有効な既存語彙であり、コマンド名へ置換しない。

### 実行と検証

このディレクトリで実行する。Python 3.11以上、標準ライブラリのみ。

```sh
python3 kitc.py examples/rena-play.kit --shell cmd --report > saikai-env.cmd
python3 kitc.py examples/rena-play.kit --shell ps
python3 kitc.py examples/rena-play.kit --shell inline
python3 -m unittest discover -s tests -v
```

`--shell cmd/ps/sh` は未指定の管理対象環境変数を消す行も出す。`--no-clear` はその解除。`--report` は出どころ・注記・警告を標準エラーへ出す。`inertia file=...` は既存のファイル読み直しを使い、キット全体のホットリロードを提供するものではない。

実パーサー照合は外部のRust検証器を使う任意試験。Cargoと指定toolchain、固定版saikaiの取得が必要になる。詳細は [oracle/run.sh](oracle/run.sh) と [tests/test_kitc.py](tests/test_kitc.py) を参照。

```sh
KITC_ORACLE=1 python3 -m unittest discover -s tests -v
```

Python試験、Rustパーサー受理、ゲームへの設置、実機動作、巻き戻し一致は別の検証。スキップや静的検査を実機の成功に数えない。過去の結果は [履歴](notes/change-history.md) に基準版とともに保存する。

### 既知の制約

無効な層への設定は警告と省略になる経路があるため、v0では `--report` を確認する。全項目の型検査、外部ファイル内容を含む設定ハッシュ、出どころの厳密な検査にも未完了箇所がある。[v0の既知の制約](design/implementation.md#3-v0の既知の制約)を参照。統合設計の「未対応要求を黙って変換しない」という契約の全面実装ではない。

## 設計の目的

単なる数値表より広く、汎用スクリプトより狭い、**型付きの状態遷移と時間計画**を目指す。技の構成・性能・時間・条件・資源・局所状態・遷移を宣言し、フック、原作への介入、処理順、状態の寿命と復元はruntimeが引き受ける。

フレーム直指定・イベント相対・区間境界・元演目位置を同格に扱う。技の仕様と実装済み能力を照合し、似た挙動への無断の置換をしない。新しい機能の表現範囲は [責務定義](design/README.md) を基準にする。

## 調査資料

[レナの既存構造](notes/rena-kit-current.md) と [個別調整の接点](notes/per-move-and-shot-tuning.md) は、基準版を付けた調査記録。現在のゲームHEADの保証ではない。初期の手法・結果・設計変更の経緯は [変更履歴](notes/change-history.md) から辿れる。性能例をユーザーの採用決定や実測値へ昇格させない。
