# 時間・モーション・キャンセル

**状態：提案・未実装。** フレーム直指定も第一級の調整方法。すべての数値は意味論を説明する仮定であり、既存技の実測ではない。

[責務](README.md) / [記法](language.md) / [イベント](events.md) / [実装計画](implementation.md)

## 1. 四つの時間座標

| 指定 | 例 | 調整への追従 |
|---|---|---|
| 技・段開始からの絶対フレーム | `18f` | 発生を変更しても18Fのまま |
| 実イベント相対 | `fire:first+2f` | 今回の実発射へ追従 |
| 調整後の区間境界 | `recovery.start+3f` | 硬直区間の変更へ追従 |
| 元の演目位置 | `source(attack,8f)` | 固定sourceの位置を変形後へ写す |

`planned:fire:first` は予定発射位置で、実発射ではない。元位置は名前付き区間と固定カタログを使い、生action番号やアドレスは書かない。

```text
cancel into=retreat from=planned:fire:first-2f before=move_end
```

予定・区間・sourceからの逆算は可能。未来の実命中を起点とする `hit:first-2f` は拒否する。開始前の時刻を0へ丸めない。分岐・ループで一意に解決しない予定位置には経路・走査回を要求する。

## 2. 時計と端点

`clock=move` は技の論理更新で、ヒットストップ中は停止する提案。アニメ速度では加速しない。`clock=battle` は同じ実行開始を原点とした戦闘更新で、actorが停止していても戦闘更新があれば進む。段内はその段開始を原点とする。描画回数や壁時計は使わない。

source座標は上記とは別で、retimeの対象。リロードや入力バッファにもそれぞれ固定された時計契約を持たせ、同じ `f` だから同じ進み方だと推測しない。

```text
cancel to-sub into=boomerang input=サブ from=18f through=32f
cancel to-sub into=boomerang input=サブ from=18f before=33f
```

上の二行は代替表記で同時指定しない。18〜32Fの15更新分の名目窓。`from` は含む、`through` は含む、`before` は含まない。両方の終端は書けない。内部は一つの半開区間へ正規化する。

終端省略は、技内なら `move_end`、段内なら `stage_end`。終了・中断後に窓を残さない。実際の開始には入力・資源・状態・実行gateも必要。

`duration=12f` は長さ、`from=12f` は12番目の判定。`frames startup=14f` は最初のactionを1Fとして14回目の技更新で攻撃効果が生じる目標。`frames total=28f` は28更新を占め、次の自由判定は29F相当。単純な一経路における定義で、途中の中断は別。

## 3. 窓・条件・入力保存を分ける

```text
cancel hit-route into=rush input=特格 from=18f through=30f require=hit:first buffer=4f
```

窓は18〜30Fで固定。命中済みは追加条件。命中した時刻へ窓を移す指定ではない。`buffer=4f` は入力を最大4F先の判定まで保持し、窓を拡張しない。18Fの判定へ14Fの入力は届くが13Fは届かない。

bufferの時計は指定または固定継承する。ヒットストップ中に入力を保存できることと、その最中に遷移を実行できることは別。保留要求は技/段の実行IDへ結び付け、終了時に失効させ、実行時に資源と条件を再検査する。

## 4. 発生時刻と観測位相

基本例は「入力判定→action→実績観測」。14F目のactionで発射が成立した場合：

| 指定 | 最早の判定例 |
|---|---|
| `from=14f` | 14Fのaction前。発射前に取り消せる |
| `from=fire:first` | 観測後の最初のgate。通常15F |
| `from=fire:first+1f` | 通常15F |
| `from=fire:first+2f` | 通常16F |
| `from=14f require=fire:first` | 時刻条件と実績が揃う通常15F |

`+Nf` は発生フレーム序数への加算で、サブフレームからN更新待つ意味ではない。目標序数へ達しても、イベント未観測なら開かない。遅延観測の場合も過去へ遡らない。

この表は位相契約の例。原作の全actorを一括フェーズへ並べ直す要求ではない。実際の更新順と安全なgateをadapterが記述し、同じ記法を無断で同tick再判定へ変えない。発生時刻が不明なら、正確な発生相対指定を受理しない。

## 5. 三種類のモーション編集

### frames：ゲーム上の目標

```text
frames startup=14f recovery=12f
```

発生は時点、硬直は長さ。他の攻撃区間・性能を保持して実現できる計画を求める。複数攻撃のどれを発生にするかはカタログで一意化するか明示する。`startup`・`recovery`・`total` の矛盾を拒否する。

### retime：演目時間と結び付いた処理を変形

```text
retime part=recovery duration=12f
retime part=recovery rate=1.5x
retime part=whole rate=1.2x
retime from=source(recovery,1f) before=source(recovery,13f) duration=8f
```

代替指定の例。同じ区間に複数の編集を重ねる意味ではない。編集元は固定sourceで、前行の変形結果を次行の入力へしない。`duration` と `rate`、重なる `frames` を行順で適用しない。

関連する演技・生成・判定時点を一緒に変形する。`frames` の要求を、断りなく全体倍速へ置換しない。

### animation：見た目だけ

```text
animation part=recovery rate=1.25x
```

姿勢サンプリングだけを変更し、当たり・生成・移動・受付は変更しない。描画骨と当たりの骨が分離できない対象では未対応。早く再生が終わる場合の姿勢保持も固定契約にする。

既存の `motion move|stop|own` は慣性・移動の指定として別に残す。

## 6. 移動量との結合

```text
retime part=lunge duration=8f travel=keep-distance
retime part=lunge duration=8f travel=keep-speed
```

代替指定。前者は無衝突の基準移動量を維持し、短縮すれば速くなる。後者はmove時計あたりの基準速度を保ち、短縮すれば一般に距離が減る。

移動区間では `travel` を明示するか固定基底から継承する。原作の実装方式次第で結果を変えない。根本移動、重力、入力慣性、向き直りのどれを変形するかをplanに出す。keep-distanceは障害物や被弾を無視する意味ではない。

## 7. 変形後の説明例

仮定：発生18F、攻撃18〜20F、硬直21〜44F。`frames startup=14f recovery=12f` で攻撃区間を維持できるなら、攻撃14〜16F、硬直17〜28Fとなる。

| 窓 | 変更前 | 変更後 |
|---|---|---|
| `from=18f before=move_end` | 18〜44F | 18〜28F |
| `from=fire:first+2f before=move_end` | 20〜44F | 16〜28F |
| `from=recovery.start before=move_end` | 21〜44F | 17〜28F |

fire行は予定どおり実発射が成立し観測できる場合。未成立を予定で埋めない。静的に空になる窓は診断し、黙って動かさない。

## 8. 実行契約

source区間を解決→時間変形plan→静的アンカーを写像→実イベント参照を保持→条件・buffer・対応能力を検査、の順。変形結果から変形元を逆定義する循環は拒否する。

sourceが12→14へ進んだ際、13のmarkerを検出することと、原作の `clock == 13` の発射処理を実行することは別。局所サブステップや再開側の副作用実行が必要なら、対象ごとに検証する。世界全体への再入で代用しない。

スローで姿勢を複数回描画しても単発生成は一回。攻撃区間を0更新に潰す場合は、定義された衝突サブステップ等がなければ拒否する。複数イベントを同一更新へ写す場合も順序・衝突の意味を保持する。

source写像は有理数等で計算し、倍率の整数化・誤差はtarget契約で表示する。整数durationやexactなstartupを別のフレームへ黙って近似しない。早期終了では当たり・予約・借用・一時効果を適切に終了する。

時計、sourceカーソル、観測履歴、保留入力を保存・復元する。時間planは技の途中で読替えない。最初の全面更新はトレモリセット等の境界で行う。
