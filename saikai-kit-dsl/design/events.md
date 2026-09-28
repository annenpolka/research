# イベントと実行契約

**状態：提案・未実装。** イベント名とhook名は公開済みAPIではない。この文書はDSL作者の作業一覧ではなく、DSLの意味を実現する側の要件を定義する。

[責務](README.md) / [記法](language.md) / [時間](timing.md) / [実装計画](implementation.md)

## 1. 引き継いだ調査事実

基準はsaikai `33067b7f420f44fb8daf251245919f0443f0eec4` と、同版が依存を固定するKakera `9c64d6ce0869484d9e1f3fd3c851a1ebfffe2f65`。これは以前のソース調査の記録で、現在HEADの再調査や実機検証ではない。

- 再開の `cancel.rs::played/cuts` は時計・既知の発射フレーム・後続行動・空撃ち情報から判断する。汎用の実発射成立イベントを消費する構造ではない。
- Kakeraの `hit_begin` はガードされなかった命中の計算前、`hit_damage` はHP減算前、`hit_reaction` はHP減算後かつ反応への行動変更前。すべて確定後通知ではない。
- 同版の `before_update` は追加再シミュレーション更新で呼ばれない契約。`logical_input` は再シミュレーションでも呼ばれるがCPU入力更新を含まない。片方だけを全シミュレーションの時計にしない。

固定資料：[再開の依存](https://gitlab.com/hidebu-reiwa/daybreak-saikai/-/blob/33067b7f420f44fb8daf251245919f0443f0eec4/crates/saikai-runtime/Cargo.toml)、[キャンセル](https://gitlab.com/hidebu-reiwa/daybreak-saikai/-/blob/33067b7f420f44fb8daf251245919f0443f0eec4/crates/saikai-runtime/src/cancel.rs)、[命中接続](https://gitlab.com/hidebu-reiwa/daybreak-saikai/-/blob/33067b7f420f44fb8daf251245919f0443f0eec4/crates/saikai-runtime/src/hit_hook.rs)、[Kakera拡張境界](https://gitlab.com/hidebu-reiwa/daybreak-kakera/-/blob/9c64d6ce0869484d9e1f3fd3c851a1ebfffe2f65/crates/kakera-runtime/src/extension.rs)。

## 2. 六つの役割

| 役割 | 契約 |
|---|---|
| Hook | 原作の介入場所。単一所有で位相と有効期間を明示 |
| Event / Observation | 実際に起きたと確認した事実 |
| Marker | タイムライン上の予定・位置の通過。成功の証明ではない |
| State / Condition | 判定時点の状態、または記録した成立履歴の問い合わせ |
| Query / Policy | 結果確定前に同期的に返す型付きの判断 |
| Command | 次の許可されたgateで実行する操作要求 |

HP減算前のダメージ変更はQuery。命中後に派生を許すのはEventとCondition。衝突フックの途中から任意の次技を開始しない。非同期pub/subや自由な `on_hit` スクリプトに統一しない。

```text
原作接続 ── Query → 型付き結果を返す
    └─ 観測 → 意味の解決 → 実行ごとの履歴
時間plan ── Marker ───────┘
                       ↓
              条件・入力・窓を判定
                       ↓
              許可されたgateで実行
                       ↓
                  実績を再び観測
```

Kakeraは共通接続点と更新/復元境界、saikai-runtimeは演目解釈と実行の由来、rulesは純粋な判断、kitcは必要能力の列挙を担当する。再開固有の「サブ」「虹ステ」をKakeraへ押し込まず、既存trampolineも無条件に移管しない。

## 3. カタログ案

| 系統 | 名前の例 |
|---|---|
| 実行 | `move.started/ended`、`stage.started/ended` |
| 時間 | source通過、phase入場、予定marker |
| 発射 | `fire.attempted/committed/failed` |
| 弾 | `projectile.spawned/despawned` |
| 命中 | `hit.confirmed/blocked`、`damage.applied`、`reaction.committed` |
| 移動 | `ground.contact_enter/exit`、`landing.started/ended`、`locomotion.changed` |
| 停止・資源 | `hitstop.entered/exited`、`resource.spent/recovered`、`charge.ready` |
| 後続拡張 | 形態・覚醒・ターゲット・死亡・再出撃 |

全部の実装を前提にしない。絶対フレーム窓には正しい実行開始と時計があればよく、命中フックまで待たない。

## 4. 実行と由来

MoveIdは定義、MoveInstanceIdは今回の技。原作action/sequenceを渡っても同じ技内部なら同じ実行。再始動は別実行。段移行ではStageInstanceIdを更新する。入力要求だけで開始イベントを出さない。

終了理由は自然終了・cancel・被弾等の中断・再始動・死亡・破棄・unknownを区別し、分からなければunknown。CPUや原作controller起点の実行も扱い、演目だけから入力を推測しない。

弾には生成時のactor世代、Move/StageInstanceId、ShotDefId、AttackInstanceId、発射バッチ、設定版を結び付ける。命中時の所有者の現在技から逆算しない。同名技を再実行中に古い弾が当たっても、今回の命中条件へ混ざらない。

子弾は由来を継承する。反射では生成元、現在の帰属、ダメージ所有者を分ける。各観測がどの帰属を使うかを固定する。

## 5. 発射と命中

一回の発射バッチと一個の弾を区別する。同じtickだから同じバッチと推測しない。

```text
fire.attempted batch=7
  projectile.spawned A
  projectile.spawned B
fire.committed batch=7 count=2
resource.spent amount=1 cause=batch7
```

これは目標の意味。実装の具体的な確定順は接続で検証する。`committed` はそのバッチから少なくとも一個の発射効果が成立したこと。全数成功を原子的に保証する能力は別。子弾生成を新しい弾消費へ勝手に数えない。

空撃ちはattemptedとfailedで、committedなし。開始拒否は発射試行点に達したことにもならない。予約・消費は資源の規則であり、イベント名だけで実装されたことにはならない。

`hit.confirmed` はガードされなかった命中解決の成立。候補検出、正のダメージ、よろけとは別。ガードはblocked、スーパーアーマーや0ダメージでも成立した命中はconfirmed。

一命中の複数hookをHitTransactionIdへ関連付ける。結果確定前の問い合わせを呼ぶたびに命中数を増やさない。決定された反応と、実際に行動変更された反応も区別する。入れ子処理は検証されたID/stackで関連付け、最後の被弾者一件を共有しない。

## 6. 接地・状態・観測宣言

接地した履歴、現在接地中、着地硬直開始、着地硬直終了、ブースト回復は別。接地だけで着地硬直や全回復を作らない。

```text
move dive
  observe touched from=ground.contact_enter subject=self occurrence=first scope=this_move
  cancel step-after-touch into=system.step input=ステップ from=touched require=grounded
```

未実装の記法例。`system.step` と入力名も対応する登録が必要。履歴だけでなく現在も接地していることを要求する。

```text
observe released from=fire.committed batch=primary occurrence=first scope=this_move
observe landed_hit from=hit.confirmed attack=blade target=enemy occurrence=first scope=this_stage
```

`observe` はフィルタと必要最小限の履歴保存の宣言。任意コードを実行しない。`primary` 等は仮の登録名。技内の `fire:first` はthis_move、段内はthis_stageの一意な発射バッチへ展開する。

`first` はscope内の初回。対象別初回やattack実体別の集計には、上限・寿命のある明示的な観測を要求する。DSL作者に保存コードを書かせない。

## 7. イベント契約の必須項目

identity、型付きpayload、発生単位、`occurred_at`、`observed_at`、利用可能gate、検出元の版、検出精度、履歴の寿命、復元方法を持つ。正確な発生時刻が不明ならunknownまたは観測区間とし、予定で埋めない。

14Fの出来事が15Fで分かっても14Fの入力判定には戻れない。瞬間的な状態変化は更新間snapshotだけでは見逃し得る。要求精度を満たせない場合は拒否し、設定値で精度を格上げしない。

命中や生成のnative順序を保持する。actor番号やイベント名で後から並べ直さない。Command実行時に実行元の生存・入力期限・資源を再検査する。フック途中の再入は禁止。

## 8. 時間変形とスコープ

source通過は `old < marker <= new` を基本に、入場時のmarkerを別途一回処理する。ループは走査回を区別する。しかし通過を観測しても原作の副作用を実行したことにはならない。

`observe_source_crossings` と `retime_native_effects` は別能力。倍速で元の発射位置を跨いでも、実生成・発射位置・衝突・終了の挙動まで検証する。

キャンセル窓は毎回条件から評価する。open/close通知だけを真実にしない。段だけ有効な重力変更等はscopeに所有させ、被弾・死亡・復元でscopeが消えれば効果を残さない。原作フィールドを書き換える場合の所有権と復旧も必要。

## 9. 保存・復元と実行入口

保存対象：actor/技/段/弾のIDと採番状態、時計、source走査、観測履歴、発射・命中の対応、入力バッファ、保留Command、資源予約・進捗、局所状態、一時効果、設定版。

native世界と同じ境界で保存・復元する。生ポインタの値を永続IDにしない。再シミュレーションでは論理イベントを再生成し、規則も再実行する。プロセス全体の処理済み集合で発射・消費を抑止しない。

外部ログ・UI・音は別経路。予測中の結果は取消し/再描画を考慮し、不可逆通知は必要に応じて確定後へ。表示epochをゲームの安定IDと混同しない。

新しい入口案は `simulation_step_begin/end` と `save/restore_extension_state`。通常・再シミュレーション・ツール更新・CPUを含む全更新を一回ずつ通す。既存 `before_update` の契約を名前だけ変えて流用しない。

## 10. 接続の実装規律

hook中に再入し得る共通lockを保持して原作を呼ばない。必要な値をコピーし、ポインタ有効期間を越えて保持しない。同期Queryを非同期キューへ逃がさない。原作パッチの所有者は一つ。

ゲームに必要なイベントはログの間引き対象ではない。容量不足・必須観測欠落・再入違反は明示的な障害経路にし、検証結果を無効化する。I/Oやコンパイルはシミュレーションの外で行う。能力宣言、設置成功、実行時の前提をそれぞれ確認する。
