# クイックスタートガイド: Claude CodeでPromptOpsを始める

このガイドでは、Claude Codeでプロンプト改善とPromptOpsを実践するための具体的なセットアップ手順を説明します。

---

## 前提条件

- Claude Code CLIがインストール済み
- Node.js 18.0以上（フックスクリプト用）
- Git（バージョン管理用）
- Anthropic API Key

---

## フェーズ1: 基礎設定（所要時間: 15分）

### 1. CLAUDE.mdファイルの作成

**目的**: プロジェクト固有のコンテキストをClaude Codeに自動提供

**手順**:

```bash
# プロジェクトルートディレクトリで実行
cd /path/to/your/project

# CLAUDE.mdを作成
cat > CLAUDE.md << 'EOF'
# プロジェクト設定

IMPORTANT: このプロジェクトは[技術スタック]を使用しています
IMPORTANT: コーディング規約: [規約の説明]
IMPORTANT: テストコマンド: [テストコマンド]
IMPORTANT: コミットメッセージは[形式]で記述してください

## よくある問題
[問題1]: [解決策]
[問題2]: [解決策]
EOF

# 実例をコピー（このリポジトリから）
cp examples/CLAUDE.md.example ./CLAUDE.md
# その後、プロジェクトに合わせて編集
```

**確認**:
```bash
claude "このプロジェクトの技術スタックを教えて"
# → CLAUDE.mdの内容が反映されているか確認
```

### 2. グローバル設定（オプション）

すべてのプロジェクトで共通の設定を使いたい場合:

```bash
# ホームディレクトリにCLAUDE.mdを作成
cat > ~/.claude/CLAUDE.md << 'EOF'
# グローバル設定

IMPORTANT: Gitコミットメッセージは日本語で記述
IMPORTANT: コード変更前に必ずバックアップを作成
IMPORTANT: セキュリティを最優先に考慮
EOF
```

---

## フェーズ2: カスタムスラッシュコマンド（所要時間: 20分）

### 1. コマンドディレクトリの作成

```bash
mkdir -p .claude/commands
```

### 2. よく使うタスクをコマンド化

**例1: テスト実行とエラー修正**

`.claude/commands/fix-tests.md`:
```markdown
# テストを実行してエラーを修正

手順:
1. すべてのテストを実行
2. 失敗したテストのエラーメッセージを分析
3. 各エラーを修正
4. 再度テストを実行して成功を確認
5. 変更内容をサマリーで報告
```

**例2: GitHub Issue対応**

`.claude/commands/fix-issue.md`:
```markdown
# GitHub Issueを修正

使い方: /fix-issue 123

手順:
1. gh issue view $ARGUMENTS で問題の詳細を取得
2. 関連ファイルを特定
3. 修正を実装
4. テストを実行
5. 修正内容をコミット
6. Issue番号を含むコミットメッセージを作成
```

**使用例**:
```bash
claude "/fix-tests"
claude "/fix-issue 42"
```

### 3. このリポジトリの例をコピー

```bash
# 例をコピー
cp examples/slash-commands/* .claude/commands/

# 使ってみる
claude "/new-component Button"
```

---

## フェーズ3: Hooksの設定（所要時間: 30分）

### 1. Hooksディレクトリの作成

```bash
mkdir -p ~/.claude/hooks
chmod 755 ~/.claude/hooks
```

### 2. 基本的なフックスクリプトの作成

**A. TypeScript自動フォーマット**

```bash
# このリポジトリから例をコピー
cp examples/hooks/format-ts.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/format-ts.sh
```

**B. Git自動バックアップ**

```bash
cp examples/hooks/git-backup.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/git-backup.sh
```

**C. 本番環境保護**

```bash
cp examples/hooks/protect-prod.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/protect-prod.sh
```

### 3. Claude Code設定ファイルの更新

```bash
# 設定ファイルを編集
nano ~/.config/claude-code/settings.json
```

以下の内容を追加:

```json
{
  "hooks": {
    "PostToolUse": {
      "command": "~/.claude/hooks/format-ts.sh",
      "matchers": [
        {"event": "Edit|Write", "file_path": ".*\\.(ts|tsx)$"}
      ]
    },
    "PreToolUse": [
      {
        "command": "~/.claude/hooks/git-backup.sh",
        "matchers": [
          {"event": "Edit|Write"}
        ]
      },
      {
        "command": "~/.claude/hooks/protect-prod.sh",
        "matchers": [
          {"event": "Edit|Write|Bash", "file_path": ".*/production/.*"}
        ]
      }
    ]
  }
}
```

### 4. 動作確認

```bash
# フォーマットフックのテスト
claude "Create a simple TypeScript function in test.ts"
# → 自動的にPrettierが実行されることを確認

# バックアップフックのテスト
git log -1
# → "AUTO-BACKUP" コミットが作成されていることを確認
```

---

## フェーズ4: コミュニティツールの導入（所要時間: 15分）

### オプション1: severity1/claude-code-prompt-improver（推奨）

**特徴**: 軽量、質問ベース、透明性が高い

**インストール**:
```bash
# マーケットプレイス経由（推奨）
claude plugin marketplace add severity1/claude-code-marketplace
claude plugin install prompt-improver@claude-code-marketplace

# 確認
claude plugin list
```

**使用方法**:
```bash
# 曖昧なプロンプト（自動で質問される）
claude "認証機能を追加"
# → プロンプト改善ツールが質問を投げかける

# 明確なプロンプト（そのまま実行）
claude "* src/auth.ts にJWT検証関数を追加"

# 評価をスキップ（/でも可）
claude "/help"
```

### オプション2: johnpsasser/claude-code-prompt-optimizer

**特徴**: 高度な最適化、拡張思考モード

**インストール**:
```bash
# リポジトリをクローン
git clone https://github.com/johnpsasser/claude-code-prompt-optimizer.git
cd claude-code-prompt-optimizer

# 依存関係をインストール
npm install

# 環境変数を設定
export ANTHROPIC_API_KEY="your-api-key"

# ビルド
npm run build

# グローバルにインストール
npm link
```

**設定**:
```json
// ~/.config/claude-code/settings.json に追加
{
  "hooks": {
    "UserPromptSubmit": {
      "command": "claude-code-prompt-optimizer"
    }
  }
}
```

**使用方法**:
```bash
# <optimize>タグを付ける
claude "<optimize> RESTful APIを実装"
# → 拡張思考モードで包括的なプロンプトに変換
```

---

## フェーズ5: 評価・最適化フレームワーク（所要時間: 1-2時間）

### DSPy（エンタープライズ向け）

**インストール**:
```bash
pip install dspy-ai anthropic
```

**クイックスタート**:
```bash
# このリポジトリの例を使用
cp examples/dspy-example.py ./
python dspy-example.py
```

**カスタマイズ**:
1. `create_training_data()`を編集してあなたのタスクに合わせたサンプルを作成
2. `accuracy_metric()`を編集して評価指標を定義
3. `CustomerSupport` Signatureを編集してタスクを定義

### AutoPrompt（少量データ向け）

**インストール**:
```bash
pip install auto-prompt langchain-anthropic
```

**クイックスタート**:
```bash
cp examples/autoprompt-example.py ./
python autoprompt-example.py
```

### LangSmith（総合ワークフロー）

**セットアップ**:
```bash
# LangSmithアカウント作成
# https://smith.langchain.com/

# APIキー取得
export LANGCHAIN_API_KEY="your-langsmith-api-key"
export LANGCHAIN_TRACING_V2=true

# LangChainとLangSmithをインストール
pip install langchain-anthropic langsmith
```

**プロンプトプレイグラウンド**:
1. https://smith.langchain.com/ にアクセス
2. "Prompts" タブを開く
3. 新しいプロンプトを作成
4. テストデータセットで評価
5. 改善を繰り返す

---

## チェックリスト: 正しくセットアップできたか確認

### ✅ 基礎設定
- [ ] CLAUDE.mdがプロジェクトルートに存在
- [ ] Claude Codeがプロジェクト固有の情報を認識している

### ✅ スラッシュコマンド
- [ ] `.claude/commands/`ディレクトリが存在
- [ ] 少なくとも1つのカスタムコマンドが動作
- [ ] `/help`でカスタムコマンドが表示される

### ✅ Hooks
- [ ] `~/.claude/hooks/`ディレクトリが存在
- [ ] スクリプトに実行権限がある（`chmod +x`）
- [ ] `~/.config/claude-code/settings.json`にフック設定が記述されている
- [ ] PostToolUseフックが動作（自動フォーマット）
- [ ] PreToolUseフックが動作（Git バックアップまたは保護）

### ✅ コミュニティツール
- [ ] 少なくとも1つのプロンプト改善ツールがインストール済み
- [ ] ツールが正常に動作することを確認

### ✅ 評価フレームワーク（オプション）
- [ ] DSPy、AutoPrompt、またはLangSmithのいずれかをセットアップ
- [ ] サンプルスクリプトが実行できる

---

## トラブルシューティング

### 問題: Hooksが実行されない

**解決策**:
1. スクリプトに実行権限があるか確認: `ls -l ~/.claude/hooks/`
2. `chmod +x ~/.claude/hooks/*.sh`を実行
3. パスが正しいか確認（`~`は展開されるか、フルパスを使用）
4. Claude Codeを再起動

### 問題: CLAUDE.mdが認識されない

**解決策**:
1. ファイル名が正確に`CLAUDE.md`（大文字）か確認
2. プロジェクトルートにあるか確認
3. Claude Codeを再起動してセッションをクリア

### 問題: スラッシュコマンドが表示されない

**解決策**:
1. `.claude/commands/`ディレクトリがプロジェクトルートにあるか確認
2. ファイルが`.md`拡張子か確認
3. `/help`を実行してコマンド一覧を確認

### 問題: プロンプト改善ツールがエラー

**解決策**:
1. `ANTHROPIC_API_KEY`環境変数が設定されているか確認: `echo $ANTHROPIC_API_KEY`
2. APIキーが有効か確認
3. Claude Code 2.0.22以降がインストールされているか確認: `claude --version`

---

## 次のステップ

1. **1週間使ってみる**: 実際のプロジェクトで基礎設定とフックを使用
2. **効果を測定**: 生産性の変化、エラー率、開発時間を記録
3. **チームで共有**: CLAUDE.mdとHooksをチームで標準化
4. **高度な機能を追加**: DSPyやAutoPromptで重要なプロンプトを最適化
5. **CI/CDに統合**: ヘッドレスモードでパイプラインに組み込む

---

## 参考リソース

- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code/)
- [Hooks完全ガイド](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)
- メインREADME: 詳細な理論と背景情報

---

## サポート

質問や問題がある場合:
1. [Claude Code GitHubリポジトリ](https://github.com/anthropics/claude-code)でIssueを検索
2. [Anthropic Discord](https://discord.gg/anthropic)でコミュニティに質問
3. このリポジトリのREADME.mdで詳細情報を確認

---

**おめでとうございます！** 🎉

これでClaude CodeでPromptOpsを実践するための基盤が整いました。
小さく始めて、徐々にワークフローを改善していきましょう。
