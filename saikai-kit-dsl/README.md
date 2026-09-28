# saikai-kit-dsl：人がキットの戦闘仕様を書くための言語

[daybreak-saikai](https://gitlab.com/hidebu-reiwa/daybreak-saikai) の技を、武装表のように読み書きするための研究。
**動作するv0の設定変換器**と、**未実装の統合設計案**を区別して置く。

## 状態と読む順序

| 資料 | 状態・読む目的 |
|---|---|
| [kitc.py](kitc.py)、[examples/](examples/) | v0の実装と入力例。既存の `SAIKAI_*` へ変換する |
| [設計の範囲と責務](design/README.md) | 統合提案の入口。「何を表現し、何を書かせないか」 |
| [記法とデータモデル](design/language.md) | 技ID、資源、局所状態、派生、条件、実験差分 |
| [時間・モーション・キャンセル](design/timing.md) | フレーム直指定、イベント相対、区間・元演目位置、時間変形 |
| [イベントと実行契約](design/events.md) | 観測と介入、実行の由来、処理位相、保存・復元 |
| [実装計画と受入条件](design/implementation.md) | 対応能力、段階導入、未解決事項、確認項目 |
| [レナの既存構造](notes/rena-kit-current.md) | saikai `abe253c` 時点の調査記録。現在のHEADの保証ではない |
| [個別調整の実装接点](notes/per-move-and-shot-tuning.md) | 当初の調査事実と、統合案による設計の訂正 |

`design/` の構文・CLI・イベント名は設計例であり、**現在の `kitc.py` には入力できない**。例の性能値・技構成は採用決定でも実測値でもない。設計案を整理したことは、ゲーム側の機能が完成したことを意味しない。

## 動機

人は「サブのリロードを遅くする」「突進の距離を保って硬直を短くする」「発射後ではなく18Fから派生させる」と技の単位で考える。設定が慣性・弾数・キャンセルなどの実装層に分散していると、技の仕様を一度に把握できない。

v0は、そのずれを**技ごとに書く→実装層ごとの設定へ変換する**ことで埋める。統合案はさらに、公開された戦闘機構を組み合わせ、技の構成・性能・時間・条件・資源・局所状態・遷移を宣言するところまでを対象にする。

原作のアドレス、フックの設置、弾生成の呼出手順、後片付け、巻き戻しの実装はDSL作者に書かせない。**戦闘仕様を書く自由は広くし、それを成立させる手続きは実行側が引き受ける。**

## 事実：v0の範囲

初期調査の基準はsaikai `abe253c`（2026-09-26）。[語彙](vocab.json)はこの時点のスナップショットで、saikai側のコードはこの試作のためには変更していない。

v0は、演目名・対象クラス・測定済み借用・依存関係・設定表の上書き・出どころを検査し、既存の環境変数へ変換する。任意の技配置、共有資源、任意キャンセルグラフ、新しいフレーム操作は未対応。

初期報告には、20個の環境変数を32行の紙で再現し、25本のテストを用意し、実パーサーのある16層で例の出力が受理されたと記録されている。これは当時の結果であり、統合案の文書整理で再実行した結果ではない。COMBO・LOCK・CAMERA・HP等の素通し部分や、ゲーム内の実動作まで検証した意味でもない。

調査手法・当時の全結果は[初期READMEの固定版](https://github.com/annenpolka/research/blob/92ad6cadc3a0ebe8d998dd8b05d52e250982cc47/saikai-kit-dsl/README.md)に残す。同版の将来案より、現在の `design/` の整理を優先する。

## 文法の英語表記

v0の見出し・項目名と、統合案の構文・コマンド・参照用IDは英語ASCII表記に統一する。説明文、`#` 以降のコメント、日本語ファイルパスはそのまま使える。統合案の引用符付き表示ラベルも日本語を許すが、v0へラベル構文を追加したわけではない。

**日本語の構文別名は廃止したため、旧 `.kit` は次の対応表で移行する。** v0は旧別名を黙って受け入れず、行番号と英語の置換先を示して拒否する。値・単位・出どころの印・コメントは変更しない。

| 旧構文の表記 | 英語表記 |
|---|---|
| メイン・`main` | `main_shot` |
| 格闘・`melee` | 一括置換不可。N格・前格・横格・下格・BD格を区別する（次節） |
| サブ | `sub_shot` |
| 特射 | `special_shot` |
| 特格 | `special_melee` |
| 射CS | `charge_shot` |
| 下格・下格闘 | `down_melee` |
| システム | `system` |
| 演目 | `perf` |
| 慣性 | `inertia` |
| 弾 | `ammo` |
| ブースト | `boost` |
| キャンセル | `cancel` |
| 空中 | `air` |
| 虹ステ | `rainbow` |

v0に既存のASCII別名 `CS` は互換のため残すが、例文と統合案では `charge_shot` を使う。これは日本語の別名を維持するものではなく、新しい略記を追加するものでもない。

## 主射撃・N格・横格の名前

公開コマンドは `main_shot`、`neutral_melee`、`up_melee`、`side_melee`、`down_melee`、`boost_dash_melee`、`sub_shot`、`special_shot`、`special_melee`、`charge_shot`。見出し、`bind`、`input=` は同じ正規名を使う。格闘5種は別コマンド・別の技定義へ解決する。

| 格闘コマンド | 意味 |
|---|---|
| `neutral_melee` | N格闘 |
| `up_melee` | 前格闘。レバー上の入力側命名 |
| `side_melee` | 左右の横格闘 |
| `down_melee` | 下格闘。既存ゲーム側の名前を維持 |
| `boost_dash_melee` | BD格闘。単なる方向入力とは別の移動状態条件 |

`down_melee` を `back_melee` へは改名しない。前格は入力側の `up` / `down` に揃えて `up_melee` とする。`front_melee`、`back_melee`、`dash_melee` は公開コマンドの別名にしない。既存の演目名 `nata.front_melee`、`nata.dash_melee`、`nata.air_dash_melee` は素材の識別子として維持し、BD格へ自動で割り当てない。命名の根拠と入力・演目の区別は [記法のコマンド定義](design/language.md#21-主射撃と方向別格闘コマンド)に記載する。

`main` は文法上の旧名として拒否する。v0の `cancel main` / `cancel main dry` も `cancel main_shot` / `cancel main_shot dry` へ移す。`melee` は以前は格闘全般をまとめていたため、`neutral_melee` の互換別名にはしない。前格・BD格などをN格または横格へ自動で含めない。

**公開文法と既存backendの名前は別。** `main_shot` の弾倉・慣性は、既存の `main=` 行へ明示的に変換する。`system` 配下の低レベル設定は従来のbackend語彙を使い、`system` の `melee side=on` や `ammo main=...`、出力の `SAIKAI_MELEE`、原作の演目ID `nata.melee` は改名しない。Gitの `main` ブランチやPythonの `main()` も変更しない。

| 項目 | 現在のv0 | 統合設計案 |
|---|---|---|
| `main_shot` と `cancel main_shot` | 対応。既存出力を維持 | 正規コマンドとして使用 |
| `neutral_melee` / `up_melee` / `side_melee` / `boost_dash_melee` | parserでは別見出しとして保持。性能指定の変換は未対応 | 独立した割当・性能・時間・キャンセルを記述 |
| 上記4種の個別設定 | `unsupported_command_split` で拒否。全格闘へ広げたり設定を捨てたりしない | controllerの方向・移動状態別役割と演目集合を接続して実行 |
| `down_melee` | 既存のキット設定への変換を維持。上記4種の未対応扱いへ含めない | 同じ公開名を維持 |

方向別見出しの空ブロックは設定を要求しないため読み取れるが、それだけで個別調整やゲーム内入力の対応が完成した意味ではない。具体例と方向の扱いは [記法のコマンド定義](design/language.md#21-主射撃と方向別格闘コマンド)を参照。

## v0の使い方

このディレクトリで実行する。Python標準ライブラリのみ。

```sh
python3 kitc.py examples/rena-play.kit --shell cmd --report > saikai-env.cmd
python3 kitc.py examples/rena-play.kit --shell ps
python3 kitc.py examples/rena-play.kit --shell inline
python3 -m unittest discover -s tests -v
```

実パーサー照合を有効にする既存コマンドは次のとおり。Rust・saikai取得などの前提は [tests/test_kitc.py](tests/test_kitc.py) と [oracle/](oracle/) を確認する。

```sh
KITC_ORACLE=1 python3 -m unittest discover -s tests -v
```

v0の記法抜粋（実行には `examples/` の完全な例を使う）：

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

`depleted/3/240/180` は撃ち切り・最大3発・通常240F・覚醒中180F。末尾の時間は空になった場合の別時間ではない。

`system` で使う層を有効にする。既知の制限として、無効な層への指定が警告と省略になり、警告表示が `--report` に依存する経路があるため、v0では報告を確認する。将来の「未対応要求は拒否」という契約とは区別する。

`--shell cmd/ps/sh` は未指定の管理対象環境変数を消す行も出す。`--no-clear` はその解除。`system` の `inertia file=...` は既存のファイル読み直しを利用するが、キット全体の安全なホットリロードを保証する機能ではない。

## 推測（示唆）：統合案の要点

**単なる数値表より広く、汎用スクリプトより狭い、型付きの状態遷移と時間計画**を目指す。上限付きの連射段、チャージ、時限強化、換装、共有資源、条件付き派生も正規の用途とする。

キャンセルの絶対フレーム指定をイベント指定の例外にしない。予定位置と実際の成立を区別し、時間変形と受付変更も別に扱う。対象実装で実現できない要求を、似た挙動へ黙って置き換えない。

## 以前の文法英語化の変更と検証（9119ec1）

`kitc.py` の日本語構文別名16個を廃止し、移行先を示す診断へ変更した。既存3例とテスト入力、設計文書の構文例・字句契約・受入条件も英語表記に揃えた。診断本文は日本語のままで、診断内の文法プレースホルダーは英語化した。

以下は今回のコマンド名変更より前の記録。検証基準は文法変更前の `fdbfe7cb1519103916a210a01960eaadcb00a21b`。次を確認した。

| 検証 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests -v` | 34件中33成功、外部Rust検証器を使う1件はスキップ |
| 既存3例の変更前後比較 | `env` と生成ファイルの内容が完全一致。性能値の変更なし |
| 英語構文の回帰検査 | 全英語見出し、日本語旧別名の拒否と置換案内、日本語コメント・パス、既存ASCII別名を確認 |
| 設計文書の構文例 | コメントと表示文字列を除きASCIIであることを字句検査。v1の意味解析・実行検証ではない |

語彙、oracle、ゲームDLL、時間・キャンセルの意味論は変更していない。Rust検証器の再実行とゲーム内検証は行っていない。`design/` の26項目は引き続き今後の受入仕様で、今回の34件のテストとは別物である。

## 以前の主射撃名・格闘区別の変更と検証（1a27da0）

変更前の基準は `9119ec150f32ddc0fed615ab304a7535f32a18b7`。主射撃を `main_shot` へ移し、N格・横格を別名として保持する。旧名は移行診断で拒否し、既存backendの `main` / `melee` 語彙は維持する。

| 検証 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests -v` | 49件中48成功、外部Rust検証器を使う1件はスキップ |
| 追加した15件の回帰テスト | 新名の識別、旧名の拒否、方向別設定の未対応診断、backendキー変換と競合検出、文書の構文例を確認 |
| 既存3例の変更前後比較 | 環境変数と生成ファイル、cmd/ps/sh/inlineの4形式の出力が完全一致 |

ゲームDLL・固定語彙・oracle・性能値は変更していない。N格・横格の方向別controller接続、拡張構文の実行、Rust検証器の再実行、実機検証は行っていない。

## 前格・BD格の追加と検証

変更前の基準は `1a27da04fbb4cc8f10a6d65b45312c4e1c929aed`。公開見出しに `up_melee` と `boost_dash_melee` を追加し、`down_melee` は維持した。パーサーでの区別と、未接続の性能指定を拒否する段階であり、ゲーム側controllerの追加ではない。

`python3 -m unittest discover -s tests -p test_up_and_boost_dash.py -v` の追加7件はすべて成功。新名の識別・重複拒否・設定の独立性・未対応診断、既存下格の出力、主射撃のbackendキー、原作演目名の維持を確認した。変更後の `kitc.py` の構文検査も成功。既存テスト全体・Rust検証器・ゲーム内動作は今回再検証していない。
