# 記法とデータモデル

**状態：統合提案・未実装。** 以下は `kitc.py` の入力例ではない。数値、`saikai.rena`、`sample.*`、段・攻撃名は説明用で、既存カタログの存在や採用済みキットを主張しない。

[責務](README.md) / [時間](timing.md) / [イベント](events.md) / [実装計画](implementation.md)

## 1. 入口と省略

```text
format 1
kit rena extends=saikai.rena
for play

メイン
  ammo constant capacity=6 reload=180f burst_reload=120f ?
  motion move

サブ boomerang "ブーメラン"
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
| Command | 認識済み入力。`サブ` は `sub_shot` の固定別名 |
| MoveId | 技の安定した識別子。配置変更でも性能が付いていく |
| PerfId | 原作から使う演目・素材 |
| ResourceId | 弾倉等の定義。残量はactorごと |
| ShotDefId / HitDefId | 技ごとの攻撃定義。原作の弾番号ではない |
| StageId / FormId | 有限の段・形態の名前 |

実行時のactor世代、MoveInstanceId、StageInstanceId、弾ID等はruntimeが作る。DSL作者が数字を管理しない。

`サブ boomerang "ブーメラン"` は `move boomerang` と `bind サブ -> boomerang` の短縮形。ラベルは表示用で参照には使わない。

```text
unbind サブ
bind 特射 -> boomerang
```

配置だけの変更で技の弾数・慣性・攻撃定義をコピーしない。同じ演目を別技で使っても独立に調整できる。backendが区別できない項目は衝突として拒否する。

`サブ` だけの見出しは固定基底で一意な技へ解決する。方向や形態で複数に分かれる場合は技IDを要求する。同一ファイル内の配置変更を見出しの解決に順次反映させない。

bindingを宣言したcommandは、その層の宣言集合で基底の集合を置き換える。条件が重複すればエラー。一つの明示的な `otherwise` は認める。行順・暗黙の詳細条件優先は使わない。移動元commandの解除は別途明示する。

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

bind 特格 -> backflip lever=neutral
bind 特格 -> rush lever=forward
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
  cancel to-sub into=boomerang input=サブ from=18f through=32f
  cancel to-rush into=rush input=特格 from=fire:first+2f before=move_end
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
    followup into=stage(second) input=メイン from=fire:first+2f before=stage_end
    cancel escape into=retreat input=特格 from=fire:first+2f before=stage_end

  stage second
    perf ground=sample.shot air=sample.air_shot
    spend ammo amount=1 at=fire:first
    followup into=stage(third) input=メイン from=fire:first+2f before=stage_end
    cancel escape into=retreat input=特格 from=fire:first+2f before=stage_end

  stage third
    perf ground=sample.finisher air=sample.air_finisher
    spend ammo amount=1 at=fire:first
    cancel escape into=retreat input=特格 from=fire:first+2f before=stage_end
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

日本語/英語の別名は固定表で正規化し、正規化後に重複を検出する。条件組合せは閉じた文法、時間式は「一つの基準±長さ」であり汎用式ではない。v0の空白splitをそのまま拡張パーサーとみなさない。

`raw` を残す場合は観測用の許可リストに限定。型付きゲーム設定を裏から上書きさせない。高度な正当な調整を `raw` に追い出す設計にはしない。
