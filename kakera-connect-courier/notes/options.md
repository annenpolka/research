# 接続手順を短くする方法の比較

[いまの手順](current-procedure.md) のどこを短くするかで分けた。評価の物差しは daybreak-kakera 側の制約。

- J36：サーバー不要のコード交換、TURN と常設マッチングは初版に入れない。
- 独自の NAT 越えや暗号は作らない。失敗したときに黙って別経路へ切り替えない。
- Windows i686（MSVC）で配布する。配布物の依存ライセンスは notices に全部載せる。

## A. コードの運び方（本命）

| 案 | 人が運ぶもの | 必要なもの | kakera の変更 | 評価 |
|---|---|---|---|---|
| **A1. 合言葉＋PAKE＋mailbox（magic-wormhole）** | 短い合言葉 1 つ、片道 | mailbox サーバー（公開のものか自前） | connector は不変。GUI か connector に運搬役を足す | **採る。** この研究で試作・検証した |
| A2. GUI の小改善（プロトコルは不変） | 長いコード 2 本のまま | なし | GUI だけ | すぐできるが、往復は残る |
| A3. 公開の pub/sub（Nostr リレー、MQTT ブローカーなど）＋部屋名 | 部屋名 1 つ | 第三者のリレー | 運搬役を足す | 部屋名がそのまま秘密になる。短くすると推測されやすく、PAKE を自分で載せると A1 を作り直すことになる |
| A4. 返信の無い一方向のコード | 招待だけ | なし | ICE の使い方を変える | **採らない。** 下の理由 |

### A1 の要点

- **合言葉が鍵になる。** magic-wormhole は合言葉で SPAKE2 を行い、以後のメッセージを導出した鍵で暗号化する。mailbox には暗号文しか届かない。合言葉を知らない相手は鍵合意に失敗する（`WrongPasswordError`）。オンラインで試せるのは 1 回の接続につき 1 回。
- **公開 mailbox がある。** Python 版は、作者が運営する公開 mailbox の URL を内蔵している（`ws://relay.magic-wormhole.io:4000/v1`）。アプリごとに appid を分ければ、他のアプリと混ざらない（[API 文書](https://magic-wormhole.readthedocs.io/en/latest/api.html)）。自前で立てるなら `magic-wormhole-mailbox-server`（pip）がある。
- **Rust で持つなら。** Rust 実装の magic-wormhole.rs は EUPL-1.2（[crates.io](https://crates.io/crates/magic-wormhole-cli/0.7.4)）。kakera の配布物に入れるなら、ライセンスの判断が要る。代わりに [`spake2` crate](https://github.com/RustCrypto/PAKEs/tree/master/spake2)（MIT／Apache-2.0、python-spake2 と互換と明記）で mailbox の最小クライアントを書き、Python の参照実装と相互に通ることを検査の条件にする道がある。
- SPAKE2 自体は RFC 9382（IRTF、2023）として公開されている（[RFC 9382](https://datatracker.ietf.org/doc/rfc9382/)）。ただし magic-wormhole の SPAKE2 は RFC より前の実装で、RFC との互換は確かめていない。

### A2 の候補（どれも connector を変えない）

- 参加側に「2人接続／4人接続」を選ばせない。招待コードの接頭辞（`kakera-connect-v2.` と `kakera-room-v1.`）で決まる。
- 期限の残り時間を画面に出す。
- 失敗したとき、次に何をすればよいかを出す（「新しい招待を作る」）。

### A4 を採らない理由

- ICE で NAT を越えるには、両側が相手の資格情報と候補を知って、両側から検査パケットを送る必要がある。
- 招待側の NAT が「送ったことのある相手からしか受けない」種類（アドレス依存・ポート依存のフィルタ）なら、招待側は参加側を知らないので届かない。
- 返信を省くには、ICE の外で独自に工夫することになる。これは「独自の NAT 越えを作らない」方針に反する。

## B. 失敗によるやり直しを減らす

失敗すると、新しい招待から全部やり直しになる。失敗そのものを減らすことも、手順を短くすることになる。

| 案 | 内容 | 評価 |
|---|---|---|
| B1. IPv6 の候補を足す | 今は IPv4 の STUN／UDP だけ。日本の IPv6 利用率は、Google の統計で 2024-02-22 に 50.57%（[日経クロステック](https://xtech.nikkei.com/atcl/nxt/column/18/02811/041700001/)。統計そのものは [Google](https://www.google.com/intl/ja/ipv6/statistics.html)） | 試す価値が高い（推測は README）。多様な回線での検証が要る |
| B2. TURN | 直接つながらない組合せを中継で救う。Cloudflare の TURN は資格情報をサーバー側で発行する設計で、「TURN key はサーバー側に置く」とある。料金は $0.05／GB（[文書](https://developers.cloudflare.com/realtime/turn/)、[資格情報](https://developers.cloudflare.com/realtime/turn/generate-credentials/)） | mailbox より重い（発行サーバーと費用）。J36 の見直しが要る。後回し |
| B3. 開いている mailbox で自動再試行 | courier の通り道が開いているうちに、失敗した接続を新しい招待・返信でやり直す | 一時的な失敗には効く。NAT の組合せが原因なら何度やっても同じ |

## C. 版をそろえる

| 案 | 内容 | 評価 |
|---|---|---|
| C1. 接続前にビルドを突き合わせる | courier の versions 交換で connector の SHA-256 と revision を比べる | **試作に入れた。** 自己申告なので、安全の仕組みではなく親切 |
| C2. 招待側の revision で取得する | 参加側の `fetch_binaries.py` に revision を渡し、checkout と取得を一度に | 小さい変更。取得先は公式の package に限られ、hash も検査するので範囲は狭い。それでも「相手が言った版を取る」ので、確認を一回はさむ |

## D. 伝送そのものを替える（今はやらない）

- **iroh**（n0 の Rust ライブラリ）：公開鍵で相手を指定して、ホールパンチを試み、だめなら relay サーバーを経由する。招待の片道化と中継を一度に得られる。ただし WebRTC で積み上げた検査（DTLS の fingerprint、DataChannel の設定、bridge の境界、12 方向の room 検査）を作り直すことになり、relay は結局サーバー。手順の改善としては大きすぎる。
- **プラットフォームのロビー**（Discord などの SDK）：招待をクリックで送れる。ただしアカウントとの結びつきが前提で、「アカウント不要」の今の設計から外れる。
