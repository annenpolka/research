# kakera-connect-courier：合言葉ひとつで繋ぐ

[daybreak-kakera](https://gitlab.com/hidebu-reiwa/daybreak-kakera)（ひぐらしデイブレイク改の非公式パッチ兼ランチャー。以下 kakera）で、ネット対戦の接続手順を短くする方法を考え、いちばん効く案を試作して確かめた。

調べたのは kakera の main `bf03c1ea`（2026-09-27）。kakera 側のコードは一行も変えていない。

## 概要

- **今の手順**：招待側が長い招待コードを作り、参加側がそれを貼って長い返信コードを作り、招待側がそれを貼る。人がチャットで 1 往復運ぶ。4 人では 6 本すべてが招待側を通る。約 5 分の期限に、この手間も含まれる。
- **提案**：招待と返信の運搬を magic-wormhole の mailbox に任せる。人は短い合言葉（例：`7-guitarist-revenge`）を、招待側から参加側へ 1 回伝えるだけになる。合言葉は SPAKE2 の鍵合意に使うので、mailbox はコードの中身を読めない。
- **試作**：`courier.py` は、変えていない `kakera-connect` を起動し、人がコピーしていたファイル（`invite.txt`・`answer.txt`）を代わりに運ぶ。
- **結果**（ループバック・ローカル mailbox）：本物の `kakera-connect` で、2 人も 4 人も接続できた。

| | 今（2 人） | courier（2 人） | 今（4 人） | courier（4 人） |
|---|---|---|---|---|
| 人が運ぶもの | 長いコード 2 本、往復 | **合言葉 1 つ、片道** | 長いコード 6 本、すべて招待側経由 | **合言葉 3 つ、片道** |
| 文字数（実測） | 646〜657 ＋ 706〜714 | **18〜20** | 689〜698 ×3 ＋ 803〜815 ×3 | **16〜21 ×3** |
| 招待側の貼り付け | 1 回 | **0 回** | 3 回（受付枠の切り替えつき） | **0 回** |
| 参加側が選ぶこと | 2人／4人 | **なし**（招待側が伝える） | 2人／4人 | **なし** |
| 約 5 分の期限が走る間 | 「招待を作る」から。人のやり取りを含む | **参加側が合言葉を入れてから** | 同左 | **最初の参加者が入れてから** |
| 版の違いが分かる時点 | 交換や接続の後 | **接続の前**（ビルドの SHA-256 を照合） | 同左 | **接続の前** |
| 合言葉を入れてから全員接続まで | — | 中央値 1.45 秒 | — | 中央値 2.66 秒 |

いまの手順を洗い出した記録は [notes/current-procedure.md](notes/current-procedure.md)、ほかの方式との比較は [notes/options.md](notes/options.md) にある。

## 動機

### 事実

- **コードは長く、人が往復で運ぶ。**
  - 招待コードと返信コードには SDP がまるごと入る（ICE の一時資格情報、候補のアドレス、DTLS の fingerprint）。zlib で圧縮しても、実物はループバックで 646〜714 文字あり、WAN の候補を足すと招待だけで約 810 文字になる見込み（推定。下の「結果」）。
  - GUI の手順は「招待を作る → コピーして渡す → 参加側が貼って参加 → 返信をコピーして返す → 招待側が貼って受け付ける」（`crates/kakera-launcher/README.md`）。
  - 別回線の二端末の検査でも、コードは「私的なファイルとチャット」で交換した（`docs/reports/internet-connect.md`）。
- **4 人では、招待側に仕事が集まる。** 招待側は受付枠を 2・3・4 と切り替えて招待を 3 本配り、届いた返信を 3 回受け付ける。
- **期限が人の手間を含む。** コード交換を含む接続期限は約 5 分。やり直すときは新しい招待から始める。招待コードの中身は connector が作るので、今の方式では connector の起動を遅らせられない。
- **方針。** J36 で「初版の接続情報はサーバー不要の招待コード・返信コードで交換する。TURN と常設マッチングは初版に含めない」と決まっている。

### 推測（示唆）

- **重いのは「長さ」より「往復」。**
  - 根拠：v2 でコードを約半分に縮めた（`docs/reports/internet-connect.md`「コードの短縮」）後も、手順の数は変わっていない。往復があると、参加側は招待を受け取るまで返信を作れない。そのため二人とも同時にチャットの前にいる必要があり、4 人では招待側が 6 回の中継点になる。
- **往復をなくすには、運搬を機械に任せるしかない。**
  - 根拠：ICE で NAT を越えるには、両側が相手の資格情報を知る必要がある。返信を省く独自の工夫は、kakera の「独自の NAT 越えを作らない」方針に反する（[notes/options.md](notes/options.md) の A4）。残るのは、返信を人ではなく機械が運ぶこと。

## 手法

1. kakera の文書から、人が手を動かす手順を数えた（[notes/current-procedure.md](notes/current-procedure.md)）。
2. 手順のどこを短くするかで方式を分け、kakera の制約と照らした（[notes/options.md](notes/options.md)）。
3. `kakera-connect` を kakera の `bf03c1ea` から Linux x86_64 で release build した（Rust 1.97.1、`cargo build --locked --release -p kakera-connect`）。今の手順（人のファイルコピー）をそのまま再現し、ループバックで `connected` まで行くことと、コードの実物の長さを確かめた。
4. 運搬役 `courier.py` を Python で書いた。magic-wormhole 0.24.0 の参照実装そのものを使い、方式の成否を先に確かめるため。kakera に入れるときは Rust に移す前提（下の「提案」）。
5. 本物の `kakera-connect` とローカルの mailbox（magic-wormhole-mailbox-server 0.8.0）で、テスト 12 本と計測を行った。テストが本当に効いているかを、実装をわざと壊して 3 回確かめた。

## courier のしくみ

```text
招待側 courier                    mailbox                     参加側 courier
合言葉を確保して表示 ──────────────(合言葉は人が伝える)──────────→ 合言葉を入力
          ←──────────── SPAKE2（合言葉が違えば両側とも失敗）──────────→
          ←──────── 版の交換（暗号化）：connector の SHA-256・revision ────→
          │                                                   └ 違えば、どちらも connector を起動せずに止まる
kakera-connect host を起動
invite.txt ──────────────── 暗号化して運ぶ ──────────────→ incoming-invite.txt
                                                          kakera-connect join（2人／4人と pregame は招待側に従う）
answer.txt ←─────────────── 暗号化して運ぶ ─────────────── answer.txt
          └──── 以後は kakera-connect どうしの ICE／DTLS。courier は中継しない ────┘
```

- **connector は不変。** courier がするのは、人がしていたファイルのコピーだけ。コードの検査（版・役割・session・返信の結び付け・サイズ）は、今までどおり `kakera-connect` が行う。courier は形（接頭辞、空白なし、96 KiB 以下）しか見ない。
- **ファイルの書き方は connector に合わせた。** 一時ファイルに書いて flush し、hard link で最終名を出す。既存のコードは上書きしない。権限は 0600。
- **秘密は stdout に出さない。** stdout は connector のイベント（そのまま転送）と、`courier_` で始まる courier のイベントだけ。合言葉は `short-code.txt`（0600）と、人が見る stderr にだけ出す。
- **4 人のとき。** 招待側は 3 つの合言葉を出す。参加者どうしの接続情報は、今までどおり connector が招待側経由の制御チャネルで交換する。courier は関わらない。

## 結果

### 事実

| 確かめたこと | 結果 | 証拠 |
|---|---|---|
| 2 人が合言葉ひとつで繋がるか | 両側 `connected`、同じ session。そのあと両方向でゲームの datagram（`KKP2P001` 封筒）が bridge を通った。停止は `stop.txt` で、両側 exit 0 | `test_pair_connects_with_one_short_code_and_carries_game_datagrams` |
| 4 人が合言葉 3 つで繋がるか | 4 者とも `connected`、`ready_edges=6`、参加者番号 1・2・3 が一致。招待側は何も貼っていない | `test_room_of_four_connects_with_three_short_codes` |
| 参加側が設定を選ばずに済むか | 招待側だけが `--pregame` を指定し、両側の `connected` に pregame の情報が付いた | `test_pregame_follows_the_host` |
| 合言葉を間違えたら | 両側 `code_mismatch` で exit 1。**どちらの connector も起動せず**、参加側に招待は書かれない | `test_a_wrong_code_fails_both_sides_before_the_joiner_starts_a_connector` |
| ビルドが違ったら | 両側 `build_mismatch` で、connector を起動する前に止まる。stderr に両方の hash と revision を出す | `test_a_different_connector_build_is_refused_before_connecting` |
| 期限が人の手間を含まないか | connector の期限を 3 秒にし、参加側が 5 秒遅れて来ても繋がった。今と同じ順（`--connector-start now`）では、connector が `connect_timeout` で失敗した | `test_a_joiner_later_than_the_connector_deadline_still_connects`、`test_today_the_connector_deadline_runs_while_the_code_is_passed` |
| 秘密が漏れないか | 全テストで、stdout に合言葉も `kakera-connect-v*.`／`kakera-room-v1.` も出ない。`short-code.txt` と `incoming-invite.txt` は 0600 | 各テストの `assert_no_secrets` |
| テストが効いているか | 実装をわざと壊すと落ちた：参加側で pregame を引き継がない、ビルド照合を外す、connector を即時起動にする（3 件とも失敗を確認して元に戻した） | 手作業の改変検査 |

計測（`tools/measure.py`、[results/measurements.json](results/measurements.json)。ペア 5 回、4 人 3 回）：

| | 合言葉 | 今のコード（招待／返信） | 合言葉を入れてから全員 `connected` まで |
|---|---|---|---|
| 2 人 | 18〜20 文字 | 646〜657／706〜714 文字 | 1.41〜1.47 秒（中央値 1.45） |
| 4 人 | 16〜21 文字 ×3 | 689〜698／803〜815 文字（各 3 本） | 2.64〜2.69 秒（中央値 2.66） |

- 時間は、Python の起動、mailbox の往復、connector の起動と候補収集、ループバックの ICE／DTLS を含む。WAN の経路や人の時間は含まない。
- connector を即時起動にした版では、2 人の中央値は 1.09 秒だった。遅延起動にすると、connector の起動と候補収集のぶん約 0.36 秒遅くなる。
- WAN の招待コードは、この環境では STUN に届かないので測れなかった。そこで、報告にある候補（host 4・srflx 2。成分 1・2 で 12 行）を実物の招待に足して、connector と同じく zlib（最高圧縮）と base64url で符号化した。**推定で約 810 文字。**

### 推測（示唆）

- **手間の削減の本体は「往復 → 片道」。**
  - 根拠：合言葉は 20 文字前後で、声でも伝えられる。参加側の courier は、招待を受け取ってから返信を返すまでを人なしで済ませる。招待側は何も貼らない。4 人でも、招待側の仕事は合言葉を 3 つ読み上げるだけになる。
- **チャットに残るものが変わる。**
  - 根拠：今は、チャットの運営者（Discord など）と、そのログを見られる人に、コードの中身が見える。コードには IP アドレス・ICE の一時資格情報・fingerprint が入っている。courier では、チャットに残るのは使い捨ての合言葉だけ。合言葉は使用後は役に立たず、PAKE なので盗み見た暗号文から総当たりもできない。
  - 代わりに、mailbox の運営者が、両側の IP アドレスと時刻と大きさを見る。そして、接続の開始が mailbox の稼働に依存する。
- **残る穴は「合言葉の横取り」。気づくのが遅い。**
  - 根拠：チャットで合言葉を見た第三者が、本物の参加者より先に使えば、招待側はその相手と繋がる。magic-wormhole は二者がそろうと番号（nameplate）を解放するので、遅れて来た本物の参加者は弾かれない。相手のいない新しい待ち合わせに入り、期限まで待ってから `code_timeout` で失敗する（`test_a_used_code_leaves_a_late_joiner_waiting_until_its_deadline`）。
  - 手当ては二つ考えられる。一つは、参加側の待ち時間を短くし、「相手が見つからない：合言葉がもう使われたか、招待側が閉じた」と出すこと。もう一つは、magic-wormhole の verifier（両側で同じになる値）を短い語にして、声で読み合わせること。どちらも試作には入れていない。
  - 今の方式でも、チャットに書き込める第三者が偽の返信を送れば、招待側はその相手と繋がりうる。その意味で、新しく開く穴ではない。ただし courier では、合言葉を見るだけで割り込める。今の方式では、招待側に偽の返信を貼らせる必要がある。この点で、少しだけ易しくなる。
- **遅延起動は courier でしかできない。**
  - 根拠：今は、人に渡す招待コードそのものを connector が作る。courier では、人に渡すのは合言葉で、合言葉は connector と無関係に作れる。だから connector の起動を、相手が来るまで待てる。

## 提案

| 段 | 変更 | 効くところ | 要る判断 |
|---|---|---|---|
| 0 | GUI の小改善：参加側の「2人／4人」をコードの接頭辞から自動で決める。期限の残り時間を出す | 迷いと時間切れが減る | なし（connector は不変） |
| **1** | **「合言葉で接続」を足す。** Rust で `kakera-connect` に運搬役を入れ（例：`--courier wormhole --relay URL`）、GUI は合言葉の表示と入力欄を持つ。今の手動コードは別の選択肢として残し、黙って切り替えない | 往復が片道に。期限と版の照合も直る | **J36 の見直し**（既定の経路が mailbox サーバーに依存する）。mailbox を公開のものにするか自前で立てるか |
| 2 | IPv4 に加えて IPv6 の候補を集める | 直接つながる組合せが増えれば、やり直しが減る | 多様な回線での検証 |
| 3 | TURN などの中継 | 直接つながらない組合せを救う | J36 の見直し、資格情報の発行サーバー、費用 |

段 1 を Rust で書くときの注意：

- magic-wormhole の Rust 実装（magic-wormhole.rs）は EUPL-1.2。配布物に入れるならライセンスの判断が要る。
- 代わりに、`spake2`（MIT／Apache-2.0）、`hkdf`・`sha2`、XSalsa20-Poly1305 の secretbox、WebSocket クライアントで、mailbox のクライアント部分だけを書く道がある。そのときは「Python の参照実装と、ローカル mailbox 上で相互に繋がる」ことを受け入れ条件にする。この研究のテストが、そのままその検査の雛形になる。
- 段 2 の IPv6 を推す根拠：日本の IPv6 利用率は Google の統計で 50% を超えている（2024-02-22 に 50.57%。[日経クロステック](https://xtech.nikkei.com/atcl/nxt/column/18/02811/041700001/)）。IPv6 には NAT が無く、家庭用ルーターはふつう「内から出た通信の戻りだけ通す」型の防火壁なので、両側から同時に送る ICE の検査は通りやすいはず。**ここは未検証の推測。**

## 使い方

```sh
# 準備
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
# kakera-connect は daybreak-kakera から build する
#   cargo build --locked --release -p kakera-connect

# 招待側（合言葉が stderr と <signal-dir>/short-code.txt に出る）
python courier.py host --connector PATH/kakera-connect --signal-dir host-session --game-port 27100
python courier.py host ... --participants 4          # 4 人（合言葉 3 つ）
python courier.py host ... --pregame                 # 対戦前同期つき。参加側は指定しなくてよい

# 参加側（2人／4人・pregame は招待側に従う）
python courier.py join --connector PATH/kakera-connect --signal-dir join-session --game-port 27100 --code 7-guitarist-revenge

# 止める：kakera-connect と同じく <signal-dir>/stop.txt を作る

# テストと計測（ローカル mailbox を自分で立てる。公開 mailbox は使わない）
KAKERA_CONNECT=PATH/kakera-connect python -m unittest discover -s tests -v
KAKERA_CONNECT=PATH/kakera-connect python tools/measure.py
```

- `--relay` の既定は公開 mailbox（`ws://relay.magic-wormhole.io:4000/v1`）。この研究では一度も使っていない。
- `--connector-start now` にすると、今と同じ順（招待を作った時点で connector を起動）になる。比較用。
- `--stun-url none` を渡すと、connector のループバック専用モードになる（テストはすべてこれ）。

## 結論

- 接続手順を短くする本筋は、コードを短くすることではない。**人が運ぶ往復をなくすこと**だった。
- 「合言葉＋PAKE＋mailbox」なら、`kakera-connect` を一行も変えずにそれができる。2 人では長いコード 2 本の往復が合言葉 1 つの片道に、4 人では招待側を通る 6 本が合言葉 3 つになった。
- おまけが二つ付いてくる。期限が人の手間を含まなくなること、版の違いが接続の前に分かること。
- 引き換えに、既定の経路が mailbox サーバーに依存する。これは J36 の「サーバー不要」を変えることなので、ユーザーの判断が要る。私の意見としては、手動コードを逃げ道として残すなら、変える価値は十分あるわ。二人が同時にチャットの前にいなければならない今の手順は、人を集める遊びにとっていちばん重い摩擦だから。

## 制限

- **Windows では動かしていない。** kakera の対象は Windows i686（MSVC）で、ここで build したのは Linux x86_64。connector の動作は同じ source から見たもの。
- **公開 mailbox、WAN、NAT は確かめていない。** すべてループバックとローカル mailbox での観測。
- **GUI には入れていない。** Python の試作で、依存（Twisted、magic-wormhole）が重い。kakera の配布物に Python の依存を持ち込む前提ではない。
- **ビルドの照合は自己申告。** 相手の申告を信じる前提で、安全の仕組みではない。
- **4 人を合言葉 1 つにする形は試していない。** 同じ合言葉を順番に使い回す形が考えられる。ただし、参加者どうしが先に鍵合意してしまう競合を解く必要があり、試作の範囲を超えた。
- 数値は説明のための観測で、性能の保証ではない。
