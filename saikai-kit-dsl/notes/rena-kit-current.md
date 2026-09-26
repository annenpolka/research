# レナのキットの今の作り（daybreak-saikai `abe253c`、2026-09-26）

DSL の設計の前に、いま動いているレナのキット（`SAIKAI_KIT=rena`）がどう組み立てられているかを追った記録。
読んだのは GitLab `hidebu-reiwa/daybreak-saikai` の main `abe253c93054f54e185b6d4b52312b3149c4ae11` のコードと文書で、実機は回していない。

## 事実

### 1. 層の積み方（上から下へ）

```text
生入力（12bit held mask）
  │  saikai-rules::commands::Recognizer（SAIKAI_COMMANDS）
  │    同時押し：射＋格＝sub_shot、射＋跳＝special_shot、格＋跳＝special_melee、3 つ＝burst（J6・J7）
  │    下格闘：キットが DownMelee を結んでいるときだけ、↓だけ＋格闘の単押し（down-melee mode）
  │    ChargeShot：溜めの層（SAIKAI_CHARGE）が満タンの離しで出す。同時押しではない
  ▼
Battle.slots[slot].queue（先行入力 BUFFER_TICKS = 6）
  │  s0.rs の before_update が毎更新 poll する
  │    出せる状態：perf::free_stance(ベースのクラス, 現在の行動)
  │      鉈：地上 0・10・27、空中 30・40・41・42（class::NATA.free_ground / free_air）
  │    例外で「出せる」に変わる場合：CS が格闘を切る（charge_cut）、メインの弾のあとの同時押し（cancel_cut, SAIKAI_CANCEL）
  │    例外で待たされる場合：跳ね上がりのあと（REACT getup=on）、BD キャンセルの閉じ（shots_closed）、弾倉（SAIKAI_AMMO の gate）
  ▼
kit::resolve_with(キット, 借用, slot, command, stance, SAIKAI_AIR)
  │  KitDef：Command → MoveId → MoveDef{ ground: PerfId, air: PerfId }
  │  SAIKAI_AIR が on なら、空中でも地上の演目を選ぶ（keep= で残すものを除く）
  ▼
perf::TABLE：PerfId → NativePerformance{ class, entry(ActionId), members, evidence, borrowing }
  │  Own：鉈自身の演目 → 行動変更 0x421080 を直接呼ぶ
  │  Borrowed：別クラスの演目 → S0 の donor（鉄塊鉈・刃こぼれした斧）のレコード・弾の表・モデルを差し替えて演じる
  ▼
原作の action（slot 6）が演じる → 各層（STEP・LOCO・INERTIA・BOOST_COST・CANCEL・AMMO…）が同じ actor のフックで重ねる
```

### 2. キットの中身（`saikai-rules::experiment::ProvisionalKit::kit()`）

| コマンド | MoveId | 地上の演目 | 空中の演目 | 演目表の行（クラス, 行動 id） | 由来 |
|---|---|---|---|---|---|
| sub_shot（射＋格） | 0 | `nata.backstep_shot` | `nata.air_shot` | 鉈 407／鉈 402→403 | 作業エージェントの選定（U14） |
| special_shot（射＋跳） | 1 | `nata.full_charge_shot` | `nata.air_full_charge_shot` | 鉈 360／鉈 370→469 | 同上（U14） |
| special_melee（格＋跳） | 2 | 既定 `iron.slide_melee` | 同じ | 鉄塊鉈 331（借用、onto 鉈、抜け先 0・43） | ユーザー判断 J9 |
| 〃 `special_melee=iron400` | 2 | `iron.shot` | 同じ | 鉄塊鉈 400（借用、弾 0・1 は donor の表） | 比較用 |
| 〃 `special_melee=ad` | 2 | `nata.air_dash_melee` | 同じ | 鉈 332→333・334（自前） | 比較用 |
| charge_shot（満タンの離し） | 3 | `nata.charge_shot` | `nata.air_charge_shot` | 鉈 450／鉈 460→469 | U14。キットが無くても `charge_kit()` で出る |
| down_melee（`down_melee=axe_main`） | 4 | `axe.shot` | `axe.air_shot` | 斧 400／斧 402（借用、`free_ammo`＝弾数無し） | ユーザー依頼 J50・J60 |

- キットの書き方は `SAIKAI_KIT` の文字列だけで、選べるのは `special_melee=slide|iron400|ad` と `down_melee=off|axe_main` の 2 項目（`ProvisionalKit::parse`）。それ以外の技の割り当ては Rust の定数で、変えるにはビルドし直す必要がある。
- `KitDef::new` の検査：結べないのは burst と guard、同じコマンドを二重に結ぶこと、演目が地上にも空中にも無い技。
- メイン（射撃の短押し）と格闘はキットに無く、原作の controller が出す（`class::NATA.roles` の 400・300 など）。キットが持つのは、同時押しと CS と下格闘の割り込みだけ。
- 演目表の各行は証拠（F の番号・run id）を持つ。別クラスの演目は、鉈へ借りた実測（`borrowing.onto == NATA`）がある行だけが借りられる。無ければ起動時に `unknown_performance`／`unmeasured_borrow` で断られる。
- 借用には上限がある。donor のクラスは戦闘に最大 2（`borrow::MAX_DONORS`）で、donor になれるのは `adapter::DONORS = [IRON, AXE]` だけ。1 演目の id は 4 まで（`MAX_IDS`）。既定のレナのキットに `down_melee=axe_main` を足すと、鉄塊鉈と斧の 2 枠がすでに埋まる。

### 3. キットの外にある、レナ固有の値

キット（KitDef）にはコマンドと演目の対応しか無い。技ごとの性質は、層ごとの設定や表に散らばっている。

| 性質 | 置き場所 | 鍵 |
|---|---|---|
| 慣性の引き継ぎ（移動撃ち・止まる・自前で動く） | `SAIKAI_INERTIA` の表（`weapon::slot_map`） | 武装の名前（`main`・`sub_shot`・`special_shot`・`special_melee`・`charge_shot`・`down_melee`・`melee`） |
| ブースト消費 | `SAIKAI_BOOST_COST` の表 | 演目の名前（`nata.shot=…`） |
| キャンセルの元と弾のフレーム | `class::NATA.mains`（鉈の短押しの射撃 6 つ、弾のフレーム 13・14） | 演目の名前 |
| CS が切る格闘 | `class::NATA.charge_cuts`（`saikai_rules::charge::MBON_CANCEL`） | 演目の名前 |
| 弾倉 | `SAIKAI_AMMO` | コマンドの名前 |
| 空中の演目を残す | `SAIKAI_AIR` の `keep=` | 演目の名前 |
| 虹ステを空中扱いにする技 | `SAIKAI_STEP` の `rainbow_air=` | 演目の名前（`perf::ALL` の 32bit） |
| 耐久値 | `SAIKAI_HP` | キャラクターの名前（`rena=`） |

- `weapon::slot_map` の引数は `Option<&ProvisionalKit>` で、レナのキットの型をそのまま受け取る。慣性の層は、レナのキットの型を直接知っている。
- 「遊びの設定」（`experiments/down-melee-axe.md` に記録された、ユーザーが手で遊ぶときの組）は、環境変数 20 個を並べたもの。

```text
SAIKAI_COMMANDS=on SAIKAI_KIT="rena down_melee=axe_main" SAIKAI_STEP="on shot=keep"
SAIKAI_LOCO="on parts=bd air=on blend=7" SAIKAI_BOOST_COST=on SAIKAI_GUARD=on
SAIKAI_MELEE="on side=on" SAIKAI_LANDING=on SAIKAI_UKEMI=on SAIKAI_HOMING="on muzzle=aim"
SAIKAI_LOCK=on SAIKAI_AIR=on SAIKAI_INERTIA=on SAIKAI_CHARGE=on SAIKAI_CANCEL=on
SAIKAI_COMBO=on SAIKAI_REACT="on getup=on" SAIKAI_BODY=on SAIKAI_AMMO=on SAIKAI_CAMERA=on
（効果のファイル・ワイド・HUD を除く）
```

### 4. 経緯（git log と台帳）

- 2026-09-23：`SAIKAI_KIT=rena` で仮キットを同時押しに載せた。同じ日に、特格を鉄塊鉈のスライド格闘へ（J9）。
- 2026-09-24：キットの形の段 0。`KitDef`／`PerfId`／演目表を作り、原作の番号は runtime へ（J11・J15）。`SAIKAI_AIR`・`SAIKAI_INERTIA`。
- 2026-09-25：`SAIKAI_CHARGE`（J32）、下格闘に斧のメイン（J50）、借りた技からの CS キャンセル（J49・J55）、空中の下格闘の急降下（J60）。
- 2026-09-26：虹ステの空中扱い `rainbow_air=`（J61）。魅音の水鉄砲をベースにする段 1（J75・J77）。レナの定数を `class::NATA` の役割へ移し始めた。
- コミットの日ごとの数は 09-22 が 10、09-23 が 42、09-24 が 296、09-25 が 692、09-26 が 213。

## 推測（示唆）

- **レナのキットは「キット」というより「割り込みの表」に近い。** 根拠：`KitDef` が持つのはコマンドと演目の対応だけで、メイン・格闘・キャンセルの経路は原作の controller のまま（kit-model.md の controller の段 1）。技の性質（慣性・消費・弾倉・キャンセルの元）は、8 か所の層の表に演目名やコマンド名を鍵にして散らばっている。人が「サブを調整したい」と思ったとき、触る場所がサブに集まっていない。
- **DSL で最初に効くのは「技ごとにまとめて書く→層ごとの設定へ転置する」ことだと思う。** 根拠：鍵がすでに演目名かコマンド名にそろっている（上の表）。だから、技ごとの記述を集めれば、今の `SAIKAI_*` の文字列へ機械的に展開できる見込みが高い。この見込みは、書式の洗い出しを終えてから確かめる。
- **キットの割り当て（どの演目をどのコマンドに結ぶか）をファイルから読むには、runtime を変える必要がある。** 根拠：`ProvisionalKit` の選択肢は 2 項目だけで、魅音の `mion_kit()` は選択肢を取らない。ただし `KitDef` はもう演目の名前だけで書けていて、名前を引く `perf::named` もある。起動時の検査（`unknown_performance`／`unmeasured_borrow`）も揃っているので、変更は小さく済むはず。
- **`weapon::slot_map(Option<&ProvisionalKit>)` は、魅音のキットを DSL で書くと最初に詰まる所になる。** 根拠：慣性の武装の行を、レナの型から作っている。`&KitDef` を受け取る形に替えれば解ける見込み。
- **借用の上限（donor 2 クラス、donor になれるのは鉄塊鉈と斧だけ）は、DSL の検査で先に弾くべき制約。** 根拠：今は起動時に `too_many_donors`／`unsupported_class` で断られ、手で遊んでいる最中に気づく形になっている。
