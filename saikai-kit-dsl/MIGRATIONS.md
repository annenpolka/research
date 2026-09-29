# 旧キットファイルの移行

現在の正規名と対応範囲は [README](README.md) と [コマンド定義](design/language.md#21-主射撃と方向別格闘コマンド) を参照。この資料は旧入力からの移行用であり、旧構文を受理する仕様ではない。実装は誤った自動変換をせず、行番号付きの診断を出す。

## 構文語の置換

コメントやパスへの一括置換ではなく、構文の位置だけを変更する。

| 旧表記 | 現在の表記 |
|---|---|
| メイン、`main` の技見出し | `main_shot` |
| `cancel main`、`cancel main dry` | `cancel main_shot`、`cancel main_shot dry` |
| 格闘、`melee` の技見出し | 対象の見直しが必要。次節を参照 |
| サブ | `sub_shot` |
| 特射 | `special_shot` |
| 特格 | `special_melee` |
| 射CS | `charge_shot` |
| 下格、下格闘 | `down_melee` |
| システム | `system` |
| 演目 | `perf` |
| 慣性 | `inertia` |
| 弾 | `ammo` |
| ブースト | `boost` |
| キャンセル | `cancel` |
| 空中 | `air` |
| 虹ステ | `rainbow` |

日本語構文の16別名は拒否対象。`main` と日本語主射撃名は同じ正規名へ移せるが、格闘全般は一つのコマンドへ移せない。v0のASCII別名 `CS` は引き続き `charge_shot` と等価。新しい入力では正規名を使う。

## 格闘全般を一つの技へ置き換えない

旧 `melee` はN格だけではなく格闘全般の設定だった。対象ごとに次の5種類へ分ける。診断もこの全候補を案内する。

| 正規名 | 対象 |
|---|---|
| `neutral_melee` | N格闘 |
| `up_melee` | 前格闘。レバー上の入力 |
| `side_melee` | 横格闘。左右の情報は別に保持 |
| `down_melee` | 下格闘。既存入力側の名前 |
| `boost_dash_melee` | BD格闘。移動状態を伴う入力 |

v0では `down_melee` の既存キットへの接続以外、上記の個別設定は未接続。`unsupported_command_split` を無視したり、格闘全体のbackend行へ戻して「同じ結果」と扱ったりしない。原作の `dash` / `air_dash` をBD格へ自動で対応付けることもしない。

`front_melee`、`back_melee`、`dash_melee` は公開コマンドの別名ではない。`up` / `down` は入力方向で、上昇・下降する動作を意味しない。

## 変更しない契約

`system` 配下の `melee side=on`、`ammo main=...`、出力先の `SAIKAI_MELEE` と `main=`、素材IDの `nata.melee` / `nata.front_melee` / `nata.dash_melee` / `nata.air_dash_melee` はそのまま使う。これらは公開コマンドとは別の名前空間である。

数値、単位、出どころの印、コメント、ファイルパス、引用符付き表示文字列を命名移行だけのために変更しない。表示ラベルは統合設計で認める文字列データであり、v0のラベル対応を意味しない。

ファイル形式の世代と機能の実装状況は別である。`unsupported_binding` は固定backendの選択肢外、`unsupported_command_split` は個別入力との未接続を表す。将来の版番号だけから実現できると判断せず、必要な接続能力を [実装計画](design/implementation.md) で確認する。

命名変更時の検証結果と旧方針の履歴は [change-history.md](notes/change-history.md) に保持する。
