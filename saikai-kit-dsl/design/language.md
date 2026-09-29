# 記法とデータモデル

**状態：統合提案・未実装。** 以下は `kitc.py` の入力例ではない。数値、`saikai.rena`、`sample.*`、段・攻撃名は説明用で、既存カタログの存在や採用済みキットを主張しない。

[責務](README.md) / [時間](timing.md) / [イベント](events.md) / [実装計画](implementation.md)

## 1. 入口と省略

**キーワード、コマンド名、項目名、列挙値、参照用IDは英語のASCII表記に統一する。** 日本語の構文別名は設けない。日本語は説明文、コメント、引用符で囲んだ表示ラベル、ファイルパスなどの文字列データに残せる。表示ラベルを技IDや入力名として解釈しない。

公開コマンドは [§2.1の一覧](#21-主射撃と方向別格闘コマンド) を正とする。システム入力の設計例 `step` はこの公開技見出し集合には含めない。旧ファイルの移行は [MIGRATIONS.md](../MIGRATIONS.md)、動作するv0の範囲は [README](../README.md) を参照。

```text
format 1
kit rena extends=saikai.rena
for play

main_shot
  ammo constant capacity=6 reload=180f burst_reload=120f ?
  motion move

sub_shot boomerang "ブーメラン"
  perf ground=nata.backstep_shot air=nata.air_shot
  ammo depleted capacity=3 reload=240f burst_reload=180f ?
  spend ammo amount=1 at=fire:first
  empty dry
  motion stop inherit=60% retain_ground=80% retain_air=85% ?
```

`format 1` は構文版であり、backendの完成段階ではない。`extends` は一つ。基底、語彙、sourceカタログ、共通rules、adapter、単位の版をlockへ記録する。実行時に「最新のon」を拾わない。

未記入は固定基底の継承。`none` は任意項目の明示的な無効化。新規定義に必須値がなければエラー。原作のままという指定も版の固定されたnative契約として解決する。

## 2. 名前と入力を分ける

| 名前 | 役割 |
|---|---|
| Command | 認識済み入力。`sub_shot` などの英語正規名で参照 |
| MoveId | 技の安定した識別子。配置変更でも性能が付いていく |
| PerfId | 原作から使う演目・素材 |
| ResourceId | 弾倉等の定義。残量はactorごと |
| ShotDefId / HitDefId | 技ごとの攻撃定義。原作の弾番号ではない |
| StageId / FormId | 有限の段・形態の名前 |

実行時のactor世代、MoveInstanceId、StageInstanceId、弾ID等はruntimeが作る。DSL作者が数字を管理しない。

`sub_shot boomerang "ブーメラン"` は `move boomerang` と `bind sub_shot -> boomerang` の短縮形。ラベルは表示用で参照には使わない。

```text
unbind sub_shot
bind special_shot -> boomerang
```

配置だけの変更で技の弾数・慣性・攻撃定義をコピーしない。同じ演目を別技で使っても独立に調整できる。backendが区別できない項目は衝突として拒否する。

`sub_shot` だけの見出しは固定基底で一意な技へ解決する。方向や形態で複数に分かれる場合は技IDを要求する。同一ファイル内の配置変更を見出しの解決に順次反映させない。

bindingを宣言したcommandは、その層の宣言集合で基底の集合を置き換える。条件が重複すればエラー。一つの明示的な `otherwise` は認める。行順・暗黙の詳細条件優先は使わない。移動元commandの解除は別途明示する。

### 2.1 主射撃と方向別格闘コマンド

| Command | 意味 | 一括して含めないもの |
|---|---|---|
| `main_shot` | 主射撃 | `special_shot` や `charge_shot` |
| `sub_shot` | サブ射撃 | 主射撃や特殊射撃 |
| `special_shot` | 特殊射撃 | 特殊格闘 |
| `special_melee` | 特殊格闘 | 方向別の通常格闘 |
| `charge_shot` | 射撃チャージ | 通常射撃の押下や自動的な多段発射 |
| `neutral_melee` | N格闘 | 横格・前格・BD格など格闘全般 |
| `up_melee` | 前格闘（レバー上の入力） | 上昇攻撃・空中格闘という動作の意味 |
| `side_melee` | 横格闘（左右） | N格・ステップ格闘・単なる横移動 |
| `down_melee` | 下格闘（既存コマンド名を維持） | 急降下・背面への攻撃という動作の意味 |
| `boost_dash_melee` | BD格闘（BD状態を伴う認識済み入力） | 原作の地上ダッシュ格闘・AD格闘との無条件な同一視 |

N格・前格・横格・下格・BD格は独立したCommand。方向の分類と地上/空中の区別は分け、姿勢ごとの演目・性能は各MoveDefで決める。BD格は移動状態を認識条件に含むため、どの姿勢・入力で成立するかと方向別格闘との競合優先順を共通rules/controllerで定義する。入力認識の実装はruntimeの責務で、DSLの識別子だけでは実現されない。

`side_melee` は左右をまとめた入力種別だが、左右方向の情報は認識時のpayloadに残す。左右共通なら一つのbinding、異なる技なら `lever=left` / `lever=right` の条件で分ける。`neutral_melee lever=left` や `up_melee lever=down` のようなコマンドと矛盾する条件は拒否し、片方を優先して読み替えない。方向名は `up` / `down` / `left` / `right` / `neutral` を基準にし、方向の座標・斜め入力の分類・BDとの優先順は固定rulesetに従う。

#### 入力側の命名と原作演目名

確認基準はsaikai `f6b6e033fa036e0f0f89f5c0eff092fc0fad6294`。
[commands.rs](https://gitlab.com/hidebu-reiwa/daybreak-saikai/-/blob/f6b6e033fa036e0f0f89f5c0eff092fc0fad6294/crates/saikai-rules/src/commands.rs) の方向ビットは `UP` / `DOWN` / `LEFT` / `RIGHT`、既存の下格コマンドは `Command::DownMelee` / `down_melee`。同版には `UpMelee` や `BoostDashMelee` のCommandはまだない。
[class.rs](https://gitlab.com/hidebu-reiwa/daybreak-saikai/-/blob/f6b6e033fa036e0f0f89f5c0eff092fc0fad6294/crates/saikai-runtime/src/class.rs) の原作格闘役割は `front`、`side`、`dash`、`air_dash` 等であり、入力コマンドとは別の名前空間である。

この入力側の `up` / `down` に合わせ、前格の公開名を `up_melee`、下格を `down_melee` とする。`front_melee` / `back_melee` を公開コマンドの別名にはしない。DSLの正規名と、固定版ゲームに実装されているCommand集合は区別する。

一方、登録済みの素材ID `nata.front_melee`、`nata.dash_melee`、`nata.air_dash_melee` 等は改名しない。`up_melee` がどの演目を使うかは明示的なbinding/MoveDefで決める。`boost_dash_melee` も原作の `dash` / `air_dash` の片方または両方へ名前だけで対応付けない。原作由来の語彙と再開の入力仕様を混ぜないための区別である。

次は独立した調整とキャンセルの構造例（未実装、固定基底に各技がある前提。性能値は提案）：

```text
neutral_melee neutral_slash "N格闘"
  frames recovery=12f ?

up_melee forward_slash "前格闘"
  frames recovery=14f ?

side_melee lateral_slash "横格闘"
  frames recovery=16f ?

boost_dash_melee dash_slash "BD格闘"
  frames recovery=18f ?

bind main_shot -> primary_fire
move primary_fire
  cancel to-neutral into=neutral_slash input=neutral_melee from=18f before=move_end
  cancel to-up into=forward_slash input=up_melee from=20f before=move_end
  cancel to-side into=lateral_slash input=side_melee from=22f before=move_end
  cancel to-bd into=dash_slash input=boost_dash_melee from=24f before=move_end
```

`input=` はCommand、`into=` はMoveIdで、同じ名前空間ではない。複数の格闘を同じ演目で演じる場合も、定義・実行元・受付窓を同一化しない。一方の調整を他方へ広げるbackendでは、その要求を拒否する。

全格闘へ共通設定を適用する機構と、一つのN格を指定する `neutral_melee` は別である。コマンドは一意な入力種別を表し、暗黙に全格闘へ適用しない。

v0では `main_shot` の設定をbackendの `main` キーへ変換し、`down_melee` は既存キットへ接続する。N格/前格/横格/BD格はパーサーで別々に保持するが、設定の変換は `unsupported_command_split` で拒否する。`system` の層名 `melee`、シリアライズ済みbackendキー、素材の `nata.melee` 等は公開Commandとは独立した契約である。

## 3. 資源

技内の `ammo` は `<kit>.<move>.ammo` という専用資源の短縮形。共有したいときだけ外へ出す。

```text
resource approach
  ammo depleted capacity=2 reload=360f burst_reload=240f ?

move backflip
  spend approach amount=1 at=start
  empty refuse

move rush
  spend approach amount=1 at=start
  empty refuse

bind special_melee -> backflip lever=neutral
bind special_melee -> rush lever=up
```

これは演目指定を省略した構造例。資源共有は各actorの内部であり、別プレイヤーとの共有ではない。

`constant` は1発ずつ回復し、追加発射で進捗を失わない。`depleted` は0から全弾回復。`never` は自動回復なし。`manual` は対応するリロード動作が必要。`burst_reload` は覚醒中の時間であり、覚醒開始時の補充とは別の設定。

発射時消費の統一モデル案：開始時に必要量を予約し、発射成立で消費確定、成立前の中断で解除する。最後の一発は実弾成立。同時発射バッチが二個の弾を出しても `amount=1` は一回分。空撃ちで開始した消費単位は、途中の回復で実弾化しない。

キャンセル時の予約解除・次技の資源検査・開始を一つの取引にする。仮の検査では旧技自身の解放予定予約を考慮できるが、次技の開始が失敗したのに旧予約だけ解除してはいけない。legacyへは実際に等価な範囲だけ変換する。

## 4. 局所状態と閉じた条件式

段、enum、上限付きカウンター、タイマー、資源、観測履歴を認める。各状態に型・初期化・寿命・終了条件を持たせる。通常の技では段と資源から自動的に決まるので、手動の変数宣言を要求しない。

条件は登録済みの読取専用述語と `all(...)` / `any(...)` / `not(...)`、型の合う比較に限る。例：

```text
require=all(grounded,resource.available(approach,1))
```

`resource.available` は言語組込みの問い合わせであり、ユーザー関数ではない。自由なメモリアクセス、関数定義、代入式、任意のイベントハンドラを導入しない。条件評価順に副作用を持たせない。

技実行内の履歴は終了時に消える。時限強化など技をまたぐ状態はactor/form等のスコープを明示する。死亡・再出撃時の扱いは型の契約に持たせる。スコープ付き効果は終了通知一個の取りこぼしで残らない構造にする。

## 5. キャンセル・追加派生・自動遷移

正規形は出発技・段の内側に置く。時間指定の意味は [timing.md](timing.md) に集約する。

```text
move main_shot
  cancel to-sub into=boomerang input=sub_shot from=18f through=32f
  cancel to-rush into=rush input=special_melee from=fire:first+2f before=move_end
```

`cancel` は入力許可。`into` はMoveIdか `system.bd` 等の予約名。`input` の省略は、目的技の入力が一意に解決するときだけ可能。route IDの省略も正規化後に一意な場合だけ認め、差分で個別編集するルートには明示IDを使う。

複数ルートは候補を作るだけで、即座にすべて実行しない。認識済み入力一件は一回だけ消費する。同一入力に異なる結果が競合する場合、共通の固定優先規則または明示priorityを要求する。ソースの行順で決めない。既定は一actorにつき一tick一回の行動遷移で、即時に次の遷移を再評価しない。追加gateを導入する場合は別の対応能力として上限と位相を定義する。

`followup` は新たな入力で同一技の次段へ進む。`transition` は入力を必要としない自動遷移。段内の `fire:first` とフレームは既定で今回の段実行を基準にする。技全体を基準にする観測は `scope=this_move` と明示する。

### 三段射撃の構造例

**未実装の設計例。** `sample.*` は仮の演目カタログ。各段には測定済みの発射バッチが一つある想定。ブースト・移動・終了姿勢等は固定基底が供給する前提で、実行可能な完成キットではない。

```text
move volley entry=first
  ammo depleted capacity=3 reload=300f ?

  stage first
    perf ground=sample.shot air=sample.air_shot
    spend ammo amount=1 at=fire:first
    followup into=stage(second) input=main_shot from=fire:first+2f before=stage_end
    cancel escape into=retreat input=special_melee from=fire:first+2f before=stage_end

  stage second
    perf ground=sample.shot air=sample.air_shot
    spend ammo amount=1 at=fire:first
    followup into=stage(third) input=main_shot from=fire:first+2f before=stage_end
    cancel escape into=retreat input=special_melee from=fire:first+2f before=stage_end

  stage third
    perf ground=sample.finisher air=sample.air_finisher
    spend ammo amount=1 at=fire:first
    cancel escape into=retreat input=special_melee from=fire:first+2f before=stage_end
```

追加段への入力は新しい入力要求。最初の入力を三回再利用しない。段末で派生しなければ技を終了する。段移行でMoveInstanceIdは維持し、StageInstanceIdを更新する。別技へのcancelは新しいMoveInstanceId。第三段には追加段がないので最大三段となる。

自動段移行の別例：`transition into=stage(recovery) when=stage_end`。終了理由が自然な段末の場合に限り、既定では次の許可されたgateで実行する。被弾を自然終了として続行しない。自然終了は安全なgateまでpending endとして保持できる実装を要求する。

上限付きの `repeat` / `sequence` を追加する場合も、このような有限計画へ展開する。任意コードのループではない。形態中の時間短縮・最終段の攻撃差分は型付きvariantとして扱う。variantの詳細構文は未確定であり、`raw` で代用しない。

## 6. 攻撃定義と生成計画

```text
move boomerang
  shot blade
    damage 1200native_hp ?
    correction subtract=20pp ?
    down 1.5dv ?
    reaction stagger
    speed multiplier=0.8x ?
    lifetime 60f ?
```

`shot blade` は登録された既存攻撃出口の調整。宣言数を増やしても弾は増えない。弾数・散布・発射時刻を変える場合は、別の生成計画と対応能力を必要とする。生成計画も言語の対象だが、具体的スキーマと原作接続は未実装。

格闘は `hit slash_1` のような登録名で指定する。`#` はコメント専用で、`nata.melee#2` のような当たり番号表記には使わない。攻撃補正の適用順、下限、丸めは共通rulesの版に従う。

## 7. 単位とモーション

| 記法 | 意味 |
|---|---|
| `capacity=3` | 無次元の整数回数 |
| `reload=240f` | その項目の時計の240更新 |
| `reload=4s` | targetのtick_hzで変換。非整数tickは拒否 |
| `inherit=60%` | 0.6の比率 |
| `subtract=20pp` | 20パーセントポイントの加算差分 |
| `multiplier=0.8x` | 固定基底に対する倍率 |
| `1200native_hp` | 原作HP尺度。表示HPを勝手に推測しない |
| `1.5dv` | 明示したダウン値尺度 |
| `30native_u/f` | 指定時計あたりの速度。距離とは別次元 |

小数は十進の正確値/有理数として読む。丸めはtarget契約で固定する。NaN、Infinity、未知単位はエラー。

`motion move|stop|own` は移動・慣性。発生等の目標は `frames`、演目時間の変形は `retime`、見た目のみは `animation` と分ける。詳しくは [timing.md](timing.md)。

## 8. 実験差分と出どころ

```text
tune slower-sub target=rena
move boomerang
  expect ammo.reload=240f
  ammo reload=300f ?
```

`expect` は差分適用前の固定基底への前提。差分はまず既存フィールドの置換に限定。複数差分が同じフィールドを書いたら、同じ値でも衝突。同一層内の二重代入もエラー。リスト要素は安定IDで指定する。

`!J<n>` は決定であるという申告、`?U<n>` と `?` は提案。`!U<n>` は拒否する。印はその行の明示値だけに付く。値を上書きしたら旧決定印を継承しない。参照先が存在することと、その値を承認していることは別に検証する。

`for play` は出どころ未分類を許す。`for run` は有効値の出どころを要求するが提案値を禁止しない。型不正・未対応の拒否はどちらでも同じ。印とコメントはゲーム挙動へ影響しない。

## 9. 最小の字句契約

UTF-8、LF/CRLF、2個のASCIIスペース単位の字下げ。タブ/全角スペースの字下げは診断する。引用符外の `#` は行末コメント。文字列は二重引用符で、`\"` と `\\` を扱う。`key=value`、`->`、行末印を別トークンとして扱う。

構文語と参照用IDには英語ASCII表記を使う。日本語の語を英語へ暗黙変換せず、診断で正規名への置換を案内する。同じ正規名の二重定義は拒否する。条件組合せは閉じた文法、時間式は「一つの基準±長さ」であり汎用式ではない。v0の空白splitをそのまま拡張パーサーとみなさない。

`raw` を残す場合は観測用の許可リストに限定。型付きゲーム設定を裏から上書きさせない。高度な正当な調整を `raw` に追い出す設計にはしない。
