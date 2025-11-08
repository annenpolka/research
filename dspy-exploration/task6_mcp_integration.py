"""
Task 6: DSPy + MCP (Model Context Protocol) 統合

Model Context Protocol (MCP)を使用して、DSPyエージェントに
ツール使用能力を追加します。Claude Desktopとの互換性もあります。
"""

import dspy
import json

print("=" * 60)
print("Task 6: DSPy + MCP統合")
print("=" * 60)

print("\n## MCPとは？")
print("-" * 60)

print("""
Model Context Protocol (MCP)は、Anthropicが開発したオープンスタンダードで、
AI アプリケーションとデータソース・ツールを接続するための統一的な方法を提供します。

### MCPの利点:
- 🔌 標準化されたツール接続
- 🔄 再利用可能なサーバー
- 🛡️ セキュアなアクセス制御
- 🌐 幅広いエコシステム

### MCPサーバーの例:
- ファイルシステムアクセス
- データベース接続（PostgreSQL, SQLiteなど）
- Git操作
- Web検索
- カスタムAPI
""")

print("\n\n## 1. DSPy + MCP の基本構成")
print("-" * 60)

print("""
DSPyのReActエージェントとMCPを組み合わせることで、
LMにツール使用能力を与えることができます。

### アーキテクチャ:
```
┌─────────────┐
│ DSPy ReAct  │  ← Think, Act, Observe
│   Agent     │
└──────┬──────┘
       │
       ↓
┌──────────────┐
│ MCP Client   │  ← ツール管理
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ MCP Servers  │  ← 実際のツール実装
│ - filesystem │
│ - database   │
│ - git        │
│ - custom...  │
└──────────────┘
```
""")

print("\n\n## 2. MCP設定ファイル")
print("-" * 60)

print("""
Claude Desktopと互換性のある設定ファイル形式:
""")

mcp_config_example = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "/path/to/allowed/directory"
            ]
        },
        "postgres": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-postgres",
                "postgresql://localhost/mydb"
            ]
        },
        "git": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-git",
                "--repository",
                "/path/to/repo"
            ]
        }
    }
}

print("\nconfig.json:")
print(json.dumps(mcp_config_example, indent=2, ensure_ascii=False))

print("\n\n## 3. DSPy ReActエージェント + MCP")
print("-" * 60)

print("""
DSPyのReActモジュールを使用してMCPツールを統合します。

```python
import dspy
from dspy.tools import Tool

# Claudeモデルの設定
lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
dspy.configure(lm=lm)

# MCPツールの定義
class FileSystemTool(Tool):
    def __init__(self):
        super().__init__(
            name="read_file",
            description="ファイルの内容を読み取る",
            parameters={
                "path": {"type": "string", "description": "ファイルパス"}
            }
        )

    def __call__(self, path: str) -> str:
        # 実際のMCPサーバーとの通信
        # ここでは簡略化
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error: {e}"

# ReActエージェントの作成
class MCPAgent(dspy.Module):
    def __init__(self, tools):
        super().__init__()
        self.tools = tools
        self.react = dspy.ReAct(tools=tools)

    def forward(self, query: str):
        return self.react(query=query)

# エージェントの使用
tools = [FileSystemTool()]
agent = MCPAgent(tools)

# クエリ実行
result = agent("README.mdの内容を要約してください")
print(result)
```
""")

print("\n\n## 4. 実用的なMCPツールの例")
print("-" * 60)

print("""
### 4.1 ファイルシステムツール
```python
class FileSystemTools:
    @staticmethod
    def read_file(path: str) -> str:
        '''ファイルを読み取る'''
        with open(path, 'r') as f:
            return f.read()

    @staticmethod
    def write_file(path: str, content: str) -> str:
        '''ファイルに書き込む'''
        with open(path, 'w') as f:
            f.write(content)
        return f"Written to {path}"

    @staticmethod
    def list_directory(path: str) -> list:
        '''ディレクトリの内容を一覧表示'''
        import os
        return os.listdir(path)
```

### 4.2 データベースツール
```python
class DatabaseTools:
    def __init__(self, connection_string):
        self.conn = connect(connection_string)

    def execute_query(self, query: str) -> list:
        '''SQLクエリを実行'''
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_schema(self) -> dict:
        '''データベーススキーマを取得'''
        # スキーマ情報を返す
        pass
```

### 4.3 Web検索ツール
```python
class WebSearchTool:
    def search(self, query: str, max_results: int = 5) -> list:
        '''Web検索を実行'''
        # 検索API (Google, Bing等) を呼び出し
        results = []
        # ... 検索実装
        return results
```
""")

print("\n\n## 5. GitHub実装例の参照")
print("-" * 60)

print("""
実際の実装例は以下のリポジトリで確認できます:

### ThanabordeeN/dspy-mcp-integration
https://github.com/ThanabordeeN/dspy-mcp-intregration

このリポジトリには以下が含まれています:
- MCP設定ファイルの例
- DSPy ReActエージェントの実装
- 複数のMCPサーバーとの統合
- 実用的なユースケース

### 主な特徴:
1. Claude Desktop互換のconfig.json
2. 複数のMCPサーバー管理
3. ReActエージェントでのツール使用
4. エラーハンドリングとログ
""")

print("\n\n## 6. Claude Code SDKとの連携")
print("-" * 60)

print("""
DSPyで構築したエージェントをClaude Code環境で使用するパターン:

### パターン1: DSPyモジュールをClaude Code Toolとして公開
```python
# dspy_tools.py
import dspy

class DataAnalyzer(dspy.Module):
    '''データ分析を行うDSPyモジュール'''
    def __init__(self):
        super().__init__()
        lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
        dspy.configure(lm=lm)
        self.analyze = dspy.ChainOfThought("data -> analysis")

    def forward(self, data: str):
        return self.analyze(data=data)

# Claude Code Toolとして使用
def analyze_data_tool(data: str) -> str:
    '''データを分析するツール'''
    analyzer = DataAnalyzer()
    result = analyzer(data=data)
    return result.analysis
```

### パターン2: MCPサーバーとしてDSPyエージェントを公開
```python
# DSPyエージェントをMCPサーバーとして実装
class DSPyMCPServer:
    def __init__(self):
        self.agent = MyDSPyAgent()

    def handle_tool_call(self, tool_name: str, args: dict):
        if tool_name == "analyze":
            return self.agent(query=args["query"])
        # ... 他のツール
```

### パターン3: ハイブリッドアプローチ
- Claude Codeで基本的なタスク実行
- 複雑な推論はDSPy最適化済みモジュールに委譲
- MCPで両者を接続
""")

print("\n\n## 7. 実装のベストプラクティス")
print("-" * 60)

print("""
### 7.1 エラーハンドリング
```python
class RobustMCPAgent(dspy.Module):
    def __init__(self, tools):
        super().__init__()
        self.tools = tools
        self.react = dspy.ReAct(tools=tools)

    def forward(self, query: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                result = self.react(query=query)
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"Error after {max_retries} attempts: {e}"
                continue
```

### 7.2 ツールの検証
```python
class ValidatedTool(Tool):
    def validate_input(self, **kwargs):
        '''入力を検証'''
        for key, value in kwargs.items():
            if key in self.required_params:
                if not self.validate_param(key, value):
                    raise ValueError(f"Invalid {key}: {value}")

    def __call__(self, **kwargs):
        self.validate_input(**kwargs)
        return self.execute(**kwargs)
```

### 7.3 ログとモニタリング
```python
import logging

class MonitoredAgent(dspy.Module):
    def __init__(self, tools):
        super().__init__()
        self.react = dspy.ReAct(tools=tools)
        self.logger = logging.getLogger(__name__)

    def forward(self, query: str):
        self.logger.info(f"Query: {query}")
        result = self.react(query=query)
        self.logger.info(f"Result: {result}")
        return result
```
""")

print("\n\n## 8. ユースケース例")
print("-" * 60)

print("""
### ケース1: コード分析アシスタント
- MCPファイルシステムでコードを読み取り
- DSPy最適化済みモジュールで分析
- Claudeの推論能力で改善提案

### ケース2: データベースクエリ生成
- MCPデータベースでスキーマ取得
- DSPyで自然言語→SQL変換
- 最適化されたクエリ生成

### ケース3: ドキュメント検索・要約
- MCP検索サーバーで関連文書検索
- DSPy RAGパイプラインで処理
- 高品質な要約を生成

### ケース4: マルチステップ自動化
- 複数のMCPツールを組み合わせ
- DSPy ReActで自律的にタスク実行
- Claudeの判断力で柔軟な対応
""")

print("\n\n" + "=" * 60)
print("まとめ")
print("=" * 60)

print("""
DSPy + MCP + Claudeの組み合わせにより:

✅ 標準化されたツール統合
✅ Claude Desktopとの互換性
✅ ReActエージェントによる自律的なツール使用
✅ DSPy最適化によるパフォーマンス向上
✅ 再利用可能なMCPサーバー
✅ セキュアで管理しやすいアーキテクチャ

技術スタック:
┌──────────────────┐
│  Claude Code SDK │  ← ユーザーインターフェース
└────────┬─────────┘
         │
┌────────▼─────────┐
│  DSPy Framework  │  ← プログラム的LM制御、最適化
└────────┬─────────┘
         │
┌────────▼─────────┐
│  MCP Protocol    │  ← ツール統合レイヤー
└────────┬─────────┘
         │
┌────────▼─────────┐
│  MCP Servers     │  ← 実際のツール実装
│  (filesystem,    │
│   database,      │
│   git, etc.)     │
└──────────────────┘

次のステップ:
1. 実際のMCPサーバーとの統合実装
2. カスタムツールの開発
3. パフォーマンスベンチマーク
4. プロダクション環境へのデプロイ
""")

if __name__ == "__main__":
    pass
