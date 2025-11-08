"""
シンプルなDSPyデモ

DSPyの基本的な構造を理解するためのシンプルなデモンストレーション。
実際のLM APIなしでもDSPyの構造を理解できます。
"""

import dspy

print("=" * 60)
print("DSPy シンプルデモ")
print("=" * 60)

print("\n1. Signatureの定義")
print("-" * 60)
print("""
Signatureは、タスクの入力と出力を定義します。
これは型安全な方法でLMへのインターフェースを定義するものです。

例:
""")

print("```python")
print("class Summarize(dspy.Signature):")
print('    """長いテキストを要約する"""')
print("    ")
print("    text: str = dspy.InputField(desc='要約するテキスト')")
print("    summary: str = dspy.OutputField(desc='要約結果')")
print("```")

# 実際に定義
class Summarize(dspy.Signature):
    """長いテキストを要約する"""

    text: str = dspy.InputField(desc="要約するテキスト")
    summary: str = dspy.OutputField(desc="要約結果")

print("\n✓ Signature定義完了")

print("\n\n2. Moduleの定義")
print("-" * 60)
print("""
Moduleは、実際のロジックを実装します。
dspy.Predictを使って、Signatureに基づいた予測を行います。

例:
""")

print("```python")
print("class TextSummarizer(dspy.Module):")
print("    def __init__(self):")
print("        super().__init__()")
print("        self.summarize = dspy.Predict(Summarize)")
print("    ")
print("    def forward(self, text: str):")
print("        return self.summarize(text=text)")
print("```")

# 実際に定義
class TextSummarizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarize = dspy.Predict(Summarize)

    def forward(self, text: str):
        return self.summarize(text=text)

print("\n✓ Module定義完了")

print("\n\n3. Chain-of-Thoughtの使用")
print("-" * 60)
print("""
Chain-of-Thoughtを使うと、推論ステップが自動的に追加されます。
これにより、より複雑な問題に対応できます。

例:
""")

print("```python")
print("class CoTSummarizer(dspy.Module):")
print("    def __init__(self):")
print("        super().__init__()")
print("        self.summarize = dspy.ChainOfThought(Summarize)")
print("    ")
print("    def forward(self, text: str):")
print("        return self.summarize(text=text)")
print("```")

class CoTSummarizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarize = dspy.ChainOfThought(Summarize)

    def forward(self, text: str):
        return self.summarize(text=text)

print("\n✓ Chain-of-Thought Module定義完了")

print("\n\n4. 複数のステップを組み合わせる")
print("-" * 60)
print("""
DSPyでは、複数のモジュールを組み合わせて、
より複雑なパイプラインを構築できます。

例:
""")

print("```python")
print("class AnalyzeAndSummarize(dspy.Module):")
print("    def __init__(self):")
print("        super().__init__()")
print('        # ステップ1: テキストを分析')
print('        self.analyze = dspy.ChainOfThought("text -> key_points")')
print('        # ステップ2: 要約を生成')
print('        self.summarize = dspy.ChainOfThought("text, key_points -> summary")')
print("    ")
print("    def forward(self, text: str):")
print("        analysis = self.analyze(text=text)")
print("        summary = self.summarize(")
print("            text=text,")
print("            key_points=analysis.key_points")
print("        )")
print("        return summary")
print("```")

print("\n\n5. DSPyの主要コンポーネント")
print("-" * 60)
print("""
■ Signature:
  - タスクの入力・出力を定義
  - InputField, OutputField で型を指定
  - ドキュメント文字列でタスクを説明

■ Module:
  - 実際のロジックを実装
  - forward()メソッドで処理を定義
  - 再利用可能なコンポーネント

■ Predict:
  - 基本的な予測モジュール
  - Signatureに基づいて予測

■ ChainOfThought:
  - 推論ステップを自動追加
  - より複雑な問題に対応

■ Optimizer:
  - プロンプトを自動最適化
  - BootstrapFewShot, MIPROv2など
  - メトリクスに基づいて改善
""")

print("\n\n6. DSPyの利点")
print("-" * 60)
print("""
✓ プログラム的な定義
  → 再利用可能、保守しやすい

✓ 型安全性
  → エラーを早期に発見

✓ 自動最適化
  → プロンプトエンジニアリングを自動化

✓ モジュール性
  → 複雑なシステムを構築しやすい

✓ 移植性
  → 異なるLM間での移植が容易

✓ 評価とテスト
  → メトリクスベースの評価が簡単
""")

print("\n\n7. 実際の使用例")
print("-" * 60)
print("""
DSPyは以下のようなタスクに適しています:

• 質問応答システム (QA)
• テキスト分類
• 情報抽出
• テキスト要約
• 翻訳
• マルチホップ推論
• RAG (Retrieval-Augmented Generation)
• エージェント型システム
""")

print("\n" + "=" * 60)
print("まとめ")
print("=" * 60)
print("""
DSPyは、言語モデルのプログラミングを体系的に行うための
フレームワークです。従来の手動プロンプティングとは異なり、
プログラム的な定義と自動最適化により、より保守しやすく
スケーラブルなLMベースのシステムを構築できます。

次のステップ:
1. 実際のLM API (OpenAI, Anthropicなど) を設定
2. 実データでモデルをトレーニング
3. 最適化機能を使ってパフォーマンス向上
4. 複雑なパイプラインを構築
""")

print("\n✓ デモ完了\n")
