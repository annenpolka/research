"""
Task 7: 実用的な統合パターン

DSPy + Claude + MCPの実用的な組み合わせパターンを示します。
実際のプロジェクトで使用できる設計パターンを提供します。
"""

print("=" * 70)
print("Task 7: 実用的な統合パターン")
print("=" * 70)

print("""
DSPy、Claude、MCPを組み合わせた実用的なアーキテクチャパターンを
紹介します。それぞれのパターンは異なるユースケースに適しています。
""")

print("\n" + "=" * 70)
print("パターン1: RAGシステム（検索拡張生成）")
print("=" * 70)

print("""
### アーキテクチャ:
```
User Query
    ↓
┌─────────────────┐
│ Query Processor │ ← DSPy Module
└────────┬────────┘
         ↓
┌─────────────────┐
│   Retriever     │ ← MCP Database/Search Server
└────────┬────────┘
         ↓
┌─────────────────┐
│  Generator      │ ← Claude Sonnet 4
└────────┬────────┘
         ↓
    Response
```

### 実装例:
```python
import dspy

class RAGSignature(dspy.Signature):
    '''検索拡張生成'''
    question: str = dspy.InputField(desc="ユーザーの質問")
    context: str = dspy.InputField(desc="検索された関連情報")
    answer: str = dspy.OutputField(desc="コンテキストに基づいた答え")
    sources: str = dspy.OutputField(desc="情報源の引用")

class RAGSystem(dspy.Module):
    def __init__(self, retriever):
        super().__init__()
        # Claudeで生成
        self.generate = dspy.ChainOfThought(RAGSignature)
        # MCPベースのレトリーバー
        self.retriever = retriever

    def forward(self, question: str, top_k: int = 5):
        # 1. 関連情報を検索（MCP経由）
        contexts = self.retriever.search(question, top_k=top_k)

        # 2. コンテキストを結合
        context_text = "\\n\\n".join([c['text'] for c in contexts])

        # 3. Claudeで回答生成
        result = self.generate(
            question=question,
            context=context_text
        )

        return result

# 使用例:
# lm = dspy.LM('anthropic/claude-sonnet-4-20250514')
# dspy.configure(lm=lm)
# rag = RAGSystem(retriever=my_mcp_retriever)
# answer = rag(question="DSPyとは何ですか？")
```

### 利点:
- 最新情報へのアクセス
- 事実に基づいた回答
- 引用による信頼性
- MCPでデータソース統合
""")

print("\n" + "=" * 70)
print("パターン2: マルチエージェントシステム")
print("=" * 70)

print("""
### アーキテクチャ:
```
┌─────────────────────────────────────┐
│      Orchestrator Agent             │ ← Claude Sonnet 4
│  (タスクの分解と調整)               │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┬──────────┐
    ↓             ↓          ↓
┌─────────┐  ┌─────────┐  ┌─────────┐
│Research │  │ Code    │  │ Writing │
│ Agent   │  │ Agent   │  │ Agent   │
└─────────┘  └─────────┘  └─────────┘
  (Sonnet)     (Haiku)      (Sonnet)
```

### 実装例:
```python
class ResearchAgent(dspy.Module):
    '''情報収集専門エージェント'''
    def __init__(self):
        super().__init__()
        self.research = dspy.ChainOfThought(
            "topic -> research_results, sources"
        )

    def forward(self, topic: str):
        return self.research(topic=topic)

class CodeAgent(dspy.Module):
    '''コード生成専門エージェント'''
    def __init__(self):
        super().__init__()
        self.generate_code = dspy.ChainOfThought(
            "requirements, context -> code, explanation"
        )

    def forward(self, requirements: str, context: str):
        return self.generate_code(
            requirements=requirements,
            context=context
        )

class WritingAgent(dspy.Module):
    '''文書作成専門エージェント'''
    def __init__(self):
        super().__init__()
        self.write = dspy.ChainOfThought(
            "content, style -> document"
        )

    def forward(self, content: str, style: str = "professional"):
        return self.write(content=content, style=style)

class OrchestratorAgent(dspy.Module):
    '''全体を調整するオーケストレーター'''
    def __init__(self):
        super().__init__()
        # 高性能モデルでオーケストレーション
        lm = dspy.LM('anthropic/claude-sonnet-4-20250514')

        with dspy.context(lm=lm):
            self.plan = dspy.ChainOfThought(
                "task -> subtasks, agent_assignments"
            )

        # 専門エージェント
        self.research_agent = ResearchAgent()
        self.code_agent = CodeAgent()
        self.writing_agent = WritingAgent()

    def forward(self, task: str):
        # タスクを分解
        plan = self.plan(task=task)

        # 各エージェントに委譲
        results = {}

        if "research" in plan.agent_assignments:
            results['research'] = self.research_agent(
                topic=plan.subtasks['research']
            )

        if "code" in plan.agent_assignments:
            results['code'] = self.code_agent(
                requirements=plan.subtasks['code'],
                context=results.get('research', '')
            )

        if "writing" in plan.agent_assignments:
            results['document'] = self.writing_agent(
                content=str(results)
            )

        return results

# 使用例:
# orchestrator = OrchestratorAgent()
# result = orchestrator(
#     task="Pythonで機械学習モデルを実装し、ドキュメントを作成"
# )
```

### 利点:
- 専門化による高品質な出力
- 並列処理でパフォーマンス向上
- モデル使い分けでコスト最適化
""")

print("\n" + "=" * 70)
print("パターン3: Self-Improvingシステム")
print("=" * 70)

print("""
### アーキテクチャ:
```
User Input
    ↓
┌─────────────────┐
│  Initial Model  │ ← DSPy Program
└────────┬────────┘
         ↓
┌─────────────────┐
│   Evaluation    │ ← Metric Function
└────────┬────────┘
         ↓
┌─────────────────┐
│  Optimization   │ ← BootstrapFewShot/MIPRO
│  (Claude Sonnet4│    (Teacher Model)
│   as Teacher)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Optimized Model │
└─────────────────┘
```

### 実装例:
```python
import dspy

class TaskSolver(dspy.Module):
    '''改善可能なタスクソルバー'''
    def __init__(self):
        super().__init__()
        self.solve = dspy.ChainOfThought("problem -> solution, explanation")

    def forward(self, problem: str):
        return self.solve(problem=problem)

def quality_metric(example, prediction, trace=None):
    '''品質評価メトリクス'''
    # 実際の評価ロジック
    # 例: 正解との一致度、詳細度、有用性など
    score = 0.0

    # 簡単な例: キーワードチェック
    if example.expected_keywords:
        for keyword in example.expected_keywords:
            if keyword.lower() in prediction.solution.lower():
                score += 1.0 / len(example.expected_keywords)

    return score

class SelfImprovingSystem:
    '''自己改善システム'''
    def __init__(self):
        # 教師モデル（高性能）
        self.teacher_lm = dspy.LM('anthropic/claude-sonnet-4-20250514')

        # 生徒モデル（効率的）
        self.student_lm = dspy.LM('anthropic/claude-3-haiku-20240307')

        self.program = TaskSolver()
        self.optimized_program = None

    def train(self, training_data, num_trials=10):
        '''トレーニングデータで最適化'''

        # 最適化器の設定
        optimizer = dspy.BootstrapFewShot(
            metric=quality_metric,
            max_bootstrapped_demos=4,
            max_labeled_demos=4,
            teacher_settings={'lm': self.teacher_lm}
        )

        # 生徒モデルで最適化
        with dspy.context(lm=self.student_lm):
            self.optimized_program = optimizer.compile(
                student=self.program,
                trainset=training_data
            )

    def solve(self, problem: str):
        '''問題を解決'''
        if self.optimized_program:
            return self.optimized_program(problem=problem)
        else:
            return self.program(problem=problem)

    def evaluate(self, test_data):
        '''テストデータで評価'''
        scores = []
        for example in test_data:
            pred = self.solve(example.problem)
            score = quality_metric(example, pred)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

# 使用例:
# system = SelfImprovingSystem()
# system.train(training_data)
# result = system.solve("新しい問題")
```

### 利点:
- 継続的な改善
- 高性能モデルの知識を低コストモデルに転移
- データ駆動の最適化
""")

print("\n" + "=" * 70)
print("パターン4: ツール統合エージェント（MCP）")
print("=" * 70)

print("""
### アーキテクチャ:
```
User Request
    ↓
┌─────────────────┐
│  ReAct Agent    │ ← DSPy ReAct + Claude
│  (Think/Act/    │
│   Observe)      │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────┐
│     MCP Tool Manager        │
└──┬────┬────┬────┬────┬────┘
   ↓    ↓    ↓    ↓    ↓
┌────┐┌────┐┌────┐┌────┐┌────┐
│File││Git ││DB  ││Web ││API │
│Sys ││    ││    ││    ││    │
└────┘└────┘└────┘└────┘└────┘
```

### 実装例:
```python
from dspy import ReAct, Tool

class FileSystemTool(Tool):
    '''ファイルシステムツール'''
    def __init__(self):
        super().__init__(
            name="filesystem",
            description="Read and write files",
            parameters={
                "action": {"type": "string", "enum": ["read", "write", "list"]},
                "path": {"type": "string"},
                "content": {"type": "string", "optional": True}
            }
        )

    def __call__(self, action: str, path: str, content: str = None):
        if action == "read":
            with open(path, 'r') as f:
                return f.read()
        elif action == "write":
            with open(path, 'w') as f:
                f.write(content)
            return f"Written to {path}"
        elif action == "list":
            import os
            return os.listdir(path)

class DatabaseTool(Tool):
    '''データベースツール'''
    def __init__(self, connection_string):
        super().__init__(
            name="database",
            description="Query database",
            parameters={
                "query": {"type": "string"}
            }
        )
        self.conn_string = connection_string

    def __call__(self, query: str):
        # データベースクエリを実行
        # 実際の実装では適切なDBライブラリを使用
        return f"Query result for: {query}"

class ToolAgent(dspy.Module):
    '''ツール使用エージェント'''
    def __init__(self, tools):
        super().__init__()
        # Claudeモデルで推論
        lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
        dspy.configure(lm=lm)

        # ReActモジュール
        self.agent = dspy.ReAct(tools=tools)

    def forward(self, task: str, max_iterations: int = 5):
        return self.agent(task=task, max_iterations=max_iterations)

# 使用例:
# tools = [
#     FileSystemTool(),
#     DatabaseTool("postgresql://localhost/mydb")
# ]
# agent = ToolAgent(tools)
# result = agent(task="README.mdを読んで要約をsummary.txtに保存")
```

### 利点:
- 実世界のシステムと連携
- MCP標準でツール再利用
- Claudeの判断力で適切なツール選択
""")

print("\n" + "=" * 70)
print("パターン5: ハイブリッドシステム")
print("=" * 70)

print("""
### アーキテクチャ:
DSPy、Claude Code SDK、MCPを全て組み合わせた最も強力なパターン

```
┌─────────────────────────────────────┐
│      Claude Code Interface          │ ← ユーザーとの対話
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    DSPy Orchestration Layer         │
│  - タスク管理                       │
│  - 最適化                           │
│  - 品質保証                         │
└────────┬────────────┬───────────────┘
         │            │
    ┌────▼────┐  ┌────▼────┐
    │ Claude  │  │  MCP    │
    │ Models  │  │ Tools   │
    └─────────┘  └─────────┘
```

### 実装例:
```python
class HybridSystem:
    '''DSPy + Claude + MCPの統合システム'''

    def __init__(self):
        # Claude設定
        self.claude_lm = dspy.LM('anthropic/claude-sonnet-4-20250514')
        dspy.configure(lm=self.claude_lm)

        # MCPツール
        self.tools = self.setup_mcp_tools()

        # DSPyコンポーネント
        self.rag_system = RAGSystem(retriever=self.tools['search'])
        self.agent = ToolAgent(tools=list(self.tools.values()))
        self.optimizer = self.setup_optimizer()

    def setup_mcp_tools(self):
        '''MCPツールのセットアップ'''
        return {
            'filesystem': FileSystemTool(),
            'database': DatabaseTool("..."),
            'search': SearchTool(),
            'git': GitTool()
        }

    def setup_optimizer(self):
        '''最適化器のセットアップ'''
        return dspy.BootstrapFewShot(
            metric=self.evaluate,
            max_bootstrapped_demos=4
        )

    def process_request(self, request: str):
        '''リクエストを処理'''

        # 1. タスクの分類
        task_type = self.classify_task(request)

        # 2. 適切なモジュールで処理
        if task_type == "qa":
            return self.rag_system(question=request)
        elif task_type == "tool_use":
            return self.agent(task=request)
        else:
            # カスタム処理
            return self.custom_process(request)

    def classify_task(self, request: str):
        '''タスクを分類'''
        # タスク分類ロジック
        pass

    def evaluate(self, example, prediction):
        '''評価メトリクス'''
        # 評価ロジック
        pass

    def improve(self, training_data):
        '''システムを改善'''
        optimized = self.optimizer.compile(
            student=self.agent,
            trainset=training_data
        )
        self.agent = optimized
```

### 統合のポイント:

1. **Claude Code**: ユーザーインターフェース
   - 自然な対話
   - コード実行環境
   - セッション管理

2. **DSPy**: ロジック層
   - プログラム的な定義
   - 自動最適化
   - 品質管理

3. **MCP**: ツール統合層
   - 標準化されたツール接続
   - 再利用可能なサーバー
   - セキュアなアクセス

4. **Claude Models**: 実行エンジン
   - 高品質な推論
   - 長いコンテキスト
   - 多言語対応
""")

print("\n" + "=" * 70)
print("ベストプラクティス")
print("=" * 70)

print("""
### 1. モデル選択
- 複雑な推論: Claude Sonnet 4
- バランス型: Claude Sonnet 3.5
- 高速処理: Claude Haiku 3
- コスト最適化: タスク別に使い分け

### 2. エラーハンドリング
- リトライロジック
- フォールバック戦略
- ログとモニタリング

### 3. 最適化
- 定期的なBootstrapping
- A/Bテスト
- メトリクスベースの評価

### 4. セキュリティ
- API keyの適切な管理
- ツールアクセスの制限
- 入力検証

### 5. スケーラビリティ
- キャッシング
- 並列処理
- レート制限の考慮
""")

print("\n" + "=" * 70)
print("まとめ")
print("=" * 70)

print("""
5つの実用的パターンを紹介しました:

1. RAGシステム - 検索拡張生成
2. マルチエージェント - 専門化と協調
3. Self-Improving - 継続的改善
4. ツール統合 - MCP経由の実世界連携
5. ハイブリッド - 全機能の統合

これらのパターンを組み合わせることで、
強力で保守しやすいAIシステムを構築できます。

次のステップ:
- 実際のプロジェクトでパターンを適用
- カスタムツールの開発
- パフォーマンスチューニング
- プロダクション環境へのデプロイ
""")

print("\n" + "=" * 70)

if __name__ == "__main__":
    pass
