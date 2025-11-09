# PDF to PNG Conversion Methods - Comparison Study

## 概要

このプロジェクトは、PythonでPDFファイルをPNG画像に変換する様々な方法を比較検証した研究です。速度、ファイルサイズ、品質、使いやすさの観点から、複数のライブラリとツールを評価しました。

## 動機

PDFをPNG画像に変換する必要性は、以下のような場面で頻繁に発生します：

- Webアプリケーションでのプレビュー表示
- ドキュメントのサムネイル生成
- 画像処理パイプラインへの統合
- OCR前処理
- アーカイブやバックアップ

しかし、Pythonには複数の変換方法が存在し、それぞれ異なる特性を持っています。このプロジェクトでは、実際に各方法を実装・テストし、どの方法がどのユースケースに適しているかを明らかにします。

## テストした方法

### 1. pdf2image

**概要**: Popplerベースの変換ライブラリ

**依存関係**:
- Python: `pdf2image` パッケージ
- システム: `poppler-utils`

**メリット**:
- シンプルで使いやすいAPI
- 高品質な出力
- 広くサポートされている

**デメリット**:
- システム依存パッケージ（poppler）が必要
- 速度は中程度

### 2. PyMuPDF (fitz)

**概要**: MuPDFベースの高速変換ライブラリ

**依存関係**:
- Python: `PyMuPDF` パッケージのみ

**メリット**:
- **最速の変換速度**
- システム依存パッケージ不要
- 豊富な機能（PDF操作全般に対応）
- メモリ効率が良い

**デメリット**:
- ライブラリサイズがやや大きい

### 3. Pillow

**概要**: Python Imaging Libraryの直接PDFサポート

**依存関係**:
- Python: `Pillow` パッケージ

**テスト結果**:
- ❌ **失敗**: Pillowの直接PDFサポートは非常に限定的
- 多くのPDFファイルを開けない

**結論**: PDF変換には推奨されない

### 4. Ghostscript

**概要**: コマンドラインツールを使用した変換

**依存関係**:
- システム: `ghostscript` (gs コマンド)

**メリット**:
- **最小のファイルサイズ**（優れた圧縮）
- 高品質な出力
- 業界標準ツール

**デメリット**:
- システム依存パッケージが必要
- コマンドライン経由での実行（やや複雑）
- 速度は中程度

## ベンチマーク結果

テスト環境で、3ページのサンプルPDF（テキスト、図形、パターンを含む）を150 DPIで変換しました。

### パフォーマンス比較

| 方法 | 変換時間 | 合計サイズ | 平均サイズ/ページ | 成功 |
|------|---------|-----------|-----------------|------|
| **PyMuPDF** | **0.116秒** ⚡ | 124.0 KB | 41.3 KB | ✓ |
| Ghostscript | 0.334秒 | **45.4 KB** 💾 | **15.1 KB** 💾 | ✓ |
| pdf2image | 0.636秒 | 125.7 KB | 41.9 KB | ✓ |
| Pillow | - | - | - | ❌ |

### 画像品質分析

すべての成功した方法が、同じ解像度（1275x1650ピクセル）の画像を生成しました：

```
Ghostscript  - 平均サイズ: 15.1 KB - 解像度: 1275x1650
PyMuPDF      - 平均サイズ: 41.3 KB - 解像度: 1275x1650
pdf2image    - 平均サイズ: 41.9 KB - 解像度: 1275x1650
```

**注目点**:
- Ghostscriptは同じ解像度でファイルサイズが約1/3（優れた圧縮アルゴリズム）
- PyMuPDFとpdf2imageは似たファイルサイズ

## 推奨事項

### 🏆 総合的な推奨: PyMuPDF

**理由**:
- 圧倒的に高速（他の方法の3-5倍）
- システム依存パッケージ不要（デプロイが容易）
- 十分な品質
- pipでインストール可能

**推奨ユースケース**:
- 大量のPDF処理
- リアルタイム変換が必要な場合
- クロスプラットフォーム対応
- コンテナ環境でのデプロイ

### 💾 ファイルサイズ重視: Ghostscript

**理由**:
- 最小のファイルサイズ（ストレージコスト削減）
- 業界標準の品質

**推奨ユースケース**:
- ストレージコストが重要
- アーカイブ/バックアップ
- ネットワーク転送が多い場合

### 📦 シンプルさ重視: pdf2image

**理由**:
- 最もシンプルなAPI
- 豊富なドキュメント
- コミュニティサポート

**推奨ユースケース**:
- プロトタイピング
- シンプルな変換タスク
- Popplerが既にインストールされている環境

## 使い方

### セットアップ

```bash
# Pythonパッケージのインストール
pip install -r requirements.txt

# システムパッケージのインストール（Ubuntu/Debian）
sudo apt-get install ghostscript poppler-utils
```

### サンプルPDFの生成

```bash
python3 create_sample_pdf.py
```

### 変換方法の比較テスト

```bash
python3 convert_comparison.py
```

### 結果の詳細分析

```bash
python3 analyze_results.py
```

## コード例

### PyMuPDF (推奨)

```python
import fitz  # PyMuPDF

def convert_pdf_to_png_pymupdf(pdf_path, output_dir, dpi=150):
    pdf_document = fitz.open(pdf_path)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=mat)
        output_path = f"{output_dir}/page_{page_num+1}.png"
        pix.save(output_path)

    pdf_document.close()
```

### pdf2image

```python
from pdf2image import convert_from_path

def convert_pdf_to_png_pdf2image(pdf_path, output_dir, dpi=150):
    images = convert_from_path(pdf_path, dpi=dpi)

    for i, image in enumerate(images):
        output_path = f"{output_dir}/page_{i+1}.png"
        image.save(output_path, "PNG")
```

### Ghostscript

```python
import subprocess

def convert_pdf_to_png_ghostscript(pdf_path, output_dir, dpi=150):
    output_pattern = f"{output_dir}/page_%d.png"

    cmd = [
        'gs',
        '-dNOPAUSE',
        '-dBATCH',
        '-sDEVICE=png16m',
        f'-r{dpi}',
        f'-sOutputFile={output_pattern}',
        pdf_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
```

## プロジェクト構成

```
pdf-to-png-conversion/
├── README.md                    # このファイル
├── requirements.txt             # Python依存関係
├── create_sample_pdf.py         # サンプルPDF生成スクリプト
├── convert_comparison.py        # 変換方法の比較テスト
├── analyze_results.py           # 結果の詳細分析
├── sample.pdf                   # テスト用サンプルPDF（生成後）
├── output/                      # 変換された画像の出力先
│   ├── PyMuPDF_page_1.png
│   ├── pdf2image_page_1.png
│   └── Ghostscript_page_1.png
└── analysis_results.json        # 分析結果（JSON形式）
```

## 主な発見

1. **速度が重要な場合**: PyMuPDFが明確な勝者（5倍以上高速）
2. **ファイルサイズが重要な場合**: Ghostscriptが最も効率的（1/3のサイズ）
3. **Pillowの直接PDFサポート**: 実用的ではない
4. **トレードオフ**: 速度とファイルサイズの間にトレードオフが存在
5. **デプロイの容易さ**: PyMuPDFはシステム依存が無く、最もデプロイしやすい

## 結論

PDF to PNG変換には、**PyMuPDF**を第一選択として推奨します。圧倒的な速度、システム依存パッケージ不要、十分な品質を提供します。

ただし、ストレージコストやネットワーク転送が重要な場合は、**Ghostscript**の優れた圧縮性能を活用することを検討してください。

## ライセンスと注意事項

このプロジェクトは実験的な研究目的です。本番環境で使用する前に、各ライブラリのライセンスと制限事項を確認してください。

- PyMuPDF: AGPL/Commercial dual license
- pdf2image: MIT License
- Ghostscript: AGPL License（商用利用には注意）
- Pillow: HPND License

## 今後の研究課題

- 異なるDPI設定での品質比較
- 大規模PDFファイルでのパフォーマンステスト
- メモリ使用量の測定
- 並列処理の実装と比較
- 画像品質の客観的評価（SSIM、PSNRなど）
