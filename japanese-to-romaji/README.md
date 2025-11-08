# 日本語→ローマ字変換ライブラリの比較研究

## 概要

このプロジェクトは、漢字を含む日本語をローマ字に変換する様々なPythonライブラリを調査・比較した研究です。主要な4つのライブラリ（pykakasi、cutlet、romkan、jaconv）について、機能、精度、パフォーマンスの観点から包括的に評価しました。

## 動機

日本語のローマ字化は、以下のような多くの用途で必要とされます：

- URL生成（日本語記事タイトルのスラッグ化）
- データベース検索の補助
- 外国人向けの読み仮名表示
- 機械翻訳の前処理
- テキスト分析やNLP処理

しかし、漢字を含む日本語のローマ字化には以下の課題があります：

1. **漢字の読み方が複雑**: 一つの漢字に複数の読み方が存在
2. **文脈依存**: 同じ漢字でも文脈によって読み方が変わる
3. **固有名詞の扱い**: 人名や地名には特殊な読み方がある
4. **外来語の扱い**: カタカナ語を元の綴りで表記するか、音写するか

このプロジェクトでは、これらの課題に対して各ライブラリがどのようにアプローチしているかを調査しました。

## 調査対象ライブラリ

### 1. pykakasi

**特徴:**
- 自己完結型のライブラリ（外部依存なし）
- 独自の辞書を使用した形態素解析
- 複数のローマ字システムをサポート（Hepburn、Kunrei、Passport）
- インストールが簡単

**使用例:**
```python
import pykakasi

kks = pykakasi.kakasi()
result = kks.convert("日本語")
romaji = ''.join([item['hepburn'] for item in result])
# 'nihongo'
```

### 2. cutlet

**特徴:**
- MeCabベースの高精度形態素解析
- 外来語の元の綴りを保持するオプション
- 複数のローマ字システムをサポート（Hepburn、Kunrei、Nihon）
- 長文での処理速度が非常に速い

**使用例:**
```python
import cutlet

katsu = cutlet.Cutlet()
romaji = katsu.romaji("日本語")
# 'Nippon go'

# 外来語スペリング使用
katsu_foreign = cutlet.Cutlet(use_foreign_spelling=True)
romaji = katsu_foreign.romaji("コーヒー")
# 'Coffee'
```

### 3. romkan

**特徴:**
- かな⇔ローマ字の相互変換に特化
- 漢字には非対応
- 軽量で高速
- 逆変換（ローマ字→かな）が可能

**使用例:**
```python
import romkan

# かな→ローマ字
romaji = romkan.to_roma("ひらがな")
# 'hiragana'

# ローマ字→かな
hiragana = romkan.to_hiragana("konnichiha")
# 'こんいちは'
```

### 4. jaconv

**特徴:**
- 文字種変換に特化（ひらがな⇔カタカナ、全角⇔半角）
- ローマ字変換機能はなし
- 高速な文字変換
- 前処理に最適

**使用例:**
```python
import jaconv

# ひらがな→カタカナ
katakana = jaconv.hira2kata("ひらがな")
# 'ヒラガナ'

# 全角→半角
hankaku = jaconv.z2h("ＡＢＣ１２３")
# 'ABC123'
```

## 実験結果

### 1. 変換精度の比較

主要な2つのライブラリ（pykakasi、cutlet）の変換結果を比較しました：

| 入力 | pykakasi | cutlet |
|------|----------|--------|
| 日本語 | nihongo | Nippon go |
| 東京タワー | toukyoutawaa | Tokyo tower |
| こんにちは世界 | konnichihasekai | Konnichiha sekai |
| 私の名前は太郎です | watashinonamaehataroudesu | Watakushi no namae wa tarou desu |
| お茶の水 | ochanomizu | Ochanomizu |

**主な違い:**
- **単語分割**: cutletは単語ごとにスペースで区切る、pykakasiは連結
- **大文字化**: cutletは各単語の先頭を大文字化
- **外来語**: cutletは外来語を元の綴りで表記可能

### 2. 特殊ケースでの精度

| ケース | 入力 | pykakasi | cutlet |
|--------|------|----------|--------|
| 助詞「は」 | 私は学生です | watashihagakuseidesu | Watakushi wa gakusei desu |
| 助詞「へ」 | 学校へ行く | gakkouheiku | Gakkou e iku |
| 助詞「を」 | 本を読む | honwoyomu | Hon wo yomu |
| 外来語 | コーヒー | koohii | Coffee (外来語モード時) |

**結果:**
- cutletは助詞の読み方を正確に判断
- cutletは外来語を元の綴りで表記可能
- pykakasiはシンプルだが文脈を考慮しない

### 3. パフォーマンスベンチマーク

#### 短文（3文字）

| ライブラリ | 平均処理時間 |
|-----------|------------|
| pykakasi | 0.00ms |
| cutlet | 0.01ms |

**比率**: cutlet/pykakasi = 3.46x（pykakasiが速い）

#### 中文（78文字）

| ライブラリ | 平均処理時間 |
|-----------|------------|
| pykakasi | 0.13ms |
| cutlet | 0.30ms |

**比率**: cutlet/pykakasi = 2.40x（pykakasiが速い）

#### 長文（1,200文字）

| ライブラリ | 平均処理時間 |
|-----------|------------|
| pykakasi | 2.20ms |
| cutlet | 4.05ms |

**比率**: cutlet/pykakasi = 1.84x（pykakasiが速い）

#### 超長文（6,000文字以上）

| ライブラリ | 平均処理時間 |
|-----------|------------|
| pykakasi | 205.57ms |
| cutlet | 26.25ms |

**比率**: cutlet/pykakasi = 0.13x（**cutletが約8倍速い！**）

#### スループット測定（1秒間）

| ライブラリ | 変換回数/秒 |
|-----------|----------|
| pykakasi | 40,122回/秒 |
| cutlet | 15,140回/秒 |

**発見:**
- 短文ではpykakasiが高速
- 長文ではcutletが圧倒的に高速（約8倍）
- cutletはMeCabの効率的な処理により、長文でスケーラビリティが高い

### 4. 機能比較表

| 機能 | pykakasi | cutlet | romkan | jaconv |
|------|----------|--------|--------|--------|
| 漢字対応 | ○ | ○ | × | × |
| かな対応 | ○ | ○ | ○ | ○ |
| ローマ字システム | Hepburn/Kunrei/Passport | Hepburn/Kunrei/Nihon | Hepburn | - |
| 外来語スペリング | × | ○ | × | × |
| 逆変換 | × | × | ○ | × |
| 形態素解析 | 独自辞書 | MeCab | × | × |
| 依存関係 | なし | MeCab辞書 | なし | なし |
| インストール難易度 | 簡単 | 中程度 | 簡単 | 簡単 |
| 長文パフォーマンス | 中 | 優 | - | - |
| 短文パフォーマンス | 優 | 中 | 優 | 優 |

## 結論と推奨事項

### 用途別推奨ライブラリ

#### 1. **一般的な用途、簡単セットアップ重視**
→ **pykakasi**

- インストールが簡単（依存関係なし）
- 短文・中文では高速
- 十分な精度

**推奨ケース:**
- プロトタイピング
- 簡易的なローマ字化
- 短いテキストの処理

#### 2. **高精度、長文処理、外来語の正確な扱い**
→ **cutlet**

- MeCabベースで高精度
- 長文で圧倒的に高速（8倍）
- 外来語を元の綴りで表記可能
- 助詞の扱いが正確

**推奨ケース:**
- 大量の文書処理
- 高精度が要求される用途
- 外国人向けコンテンツ

#### 3. **かな⇔ローマ字の相互変換**
→ **romkan**

- 軽量で高速
- 逆変換が可能

**推奨ケース:**
- 入力システム
- かなのみの処理
- ローマ字入力支援

#### 4. **文字種変換（前処理）**
→ **jaconv**

- 文字変換に特化
- 高速

**推奨ケース:**
- テキストの正規化
- 全角/半角変換
- ひらがな/カタカナ変換

### 組み合わせアプローチ

複雑な要件には複数ライブラリの組み合わせも有効：

```python
import pykakasi
import jaconv

# 1. jaconvで文字正規化
normalized = jaconv.z2h(text, kana=False, digit=True, ascii=True)

# 2. pykakasiでローマ字化
kks = pykakasi.kakasi()
result = kks.convert(normalized)
romaji = ''.join([item['hepburn'] for item in result])
```

## セットアップと実行

### 前提条件

- Python 3.7以上

### インストール

```bash
# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# ライブラリのインストール
pip install pykakasi cutlet romkan jaconv unidic-lite
```

### 実行方法

```bash
# 個別のライブラリテスト
python test_pykakasi.py
python test_cutlet.py
python test_romkan_jaconv.py

# 包括的な比較
python comparison.py

# 詳細なベンチマーク
python benchmark.py
```

## ファイル構成

```
japanese-to-romaji/
├── README.md                    # このファイル
├── test_pykakasi.py             # pykakasiのテスト
├── test_cutlet.py               # cutletのテスト
├── test_romkan_jaconv.py        # romkan/jaconvのテスト
├── comparison.py                # 包括的な比較
├── benchmark.py                 # 詳細なベンチマーク
├── requirements.txt             # 依存関係
└── venv/                        # 仮想環境
```

## 主な発見

1. **パフォーマンスはテキスト長に依存**
   - 短文: pykakasi優位（約3倍速）
   - 長文: cutlet優位（約8倍速）

2. **精度面ではcutletが優秀**
   - 助詞の扱いが正確
   - 外来語を元の綴りで表記可能
   - 単語分割が適切

3. **用途によって最適なライブラリが異なる**
   - 簡易用途: pykakasi
   - 高精度・大量処理: cutlet
   - かな変換のみ: romkan
   - 文字正規化: jaconv

4. **セットアップの容易さも重要**
   - pykakasi: 依存関係なし、即座に使用可能
   - cutlet: MeCab辞書が必要だが、unidic-liteで簡単に解決

## 今後の課題

1. **固有名詞の扱い**: 人名・地名の読み方の精度向上
2. **カスタム辞書**: 専門用語や造語への対応
3. **リアルタイム処理**: ストリーミングデータへの対応
4. **他言語対応**: 多言語混在テキストの処理

## 参考資料

- [pykakasi GitHub](https://github.com/miurahr/pykakasi)
- [cutlet GitHub](https://github.com/polm/cutlet)
- [romkan GitHub](https://github.com/soimort/python-romkan)
- [jaconv GitHub](https://github.com/ikegami-yukino/jaconv)
- [MeCab公式](https://taku910.github.io/mecab/)

## ライセンス

このリサーチプロジェクトは研究・教育目的で作成されました。各ライブラリのライセンスについては、それぞれの公式リポジトリを参照してください。

## 作成者

このプロジェクトはAIエージェント（Claude）によって自律的に実施されました。
