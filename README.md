Inspired by [Code research projects with async coding agents like Claude Code and Codex](https://simonwillison.net/2025/Nov/6/async-code-research/)
# Research

AIツール（主にClaude Code）によって実施された研究プロジェクトのコレクション。

このリポジトリは、AIエージェントが独立して実験的なコード研究を実行するための環境です。各プロジェクトはサブディレクトリに格納され、それぞれが特定の研究質問や技術的探索に取り組んでいます。

## プロジェクト一覧

<!-- [[[cog
import os
import re
from pathlib import Path

def get_projects():
    projects = []
    for item in sorted(Path('.').iterdir()):
        if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
            summary_file = item / '_summary.md'
            if summary_file.exists():
                summary = summary_file.read_text().strip()
            else:
                # プロジェクトディレクトリのREADME.mdから最初の段落を取得
                readme_file = item / 'README.md'
                if readme_file.exists():
                    content = readme_file.read_text()
                    # 最初の見出しの後の最初の段落を取得
                    lines = content.split('\n')
                    summary_lines = []
                    started = False
                    for line in lines:
                        if line.startswith('#'):
                            started = True
                            continue
                        if started and line.strip():
                            summary_lines.append(line.strip())
                            if len(summary_lines) >= 2:
                                break
                    summary = ' '.join(summary_lines) if summary_lines else 'プロジェクトの説明'
                else:
                    summary = 'プロジェクトの説明'

            projects.append({
                'name': item.name,
                'summary': summary
            })

    return projects

projects = get_projects()
if projects:
    for project in projects:
        print(f"- **[{project['name']}](./{project['name']})**: {project['summary']}")
else:
    print("*プロジェクトはまだありません*")
]]] -->
- **[beads-non-invasive-analysis](./beads-non-invasive-analysis)**: Beadsは相対的に非侵襲的だが、gitフックとマージドライバーの強制インストールにより一定の侵襲性を持つ。ただし、.beads/を.gitignoreに追加することで、元のリポジトリにコミット対象を一切増やさずに完全ローカル運用が可能。AGENTS.mdは自動変更されない。
- **[cc-sessions-mode-behavior](./cc-sessions-mode-behavior)**: このプロジェクトは、[cc-sessions](https://github.com/GWUDCAP/cc-sessions)のDAIC（Discussion-Alignment-Implementation-Check）メソドロジーにおけるモード動作とその実現方法を調査した研究です。 cc-sessionsは、Claude Codeのための構造化されたAIペアプログラミングワークフレームです。Claudeがコードを書く前に議論し、承認を得ることを強制する仕組みを提供します。
- **[claude-auto-approve-commands](./claude-auto-approve-commands)**: Claude Codeで特定のコマンドを自動許可する設定方法の調査と実装（allowedTools、defaultMode、PreToolUseフック）
- **[claude-code-hooks-observability-plugin](./claude-code-hooks-observability-plugin)**: Claude Code Hooks Multi-Agent Observability システムのPlugin化プロトタイプ - 完全に実現可能で、MCPサーバー統合により元のシステムを超える機能を提供
- **[claude-code-infrastructure-showcase](./claude-code-infrastructure-showcase)**: プロジェクトの説明
- **[claude-code-prompt-improver-analysis](./claude-code-prompt-improver-analysis)**: Claude Code Prompt Improver - 曖昧なプロンプトを自動改善するUserPromptSubmitフック（83行のPython、会話履歴活用、リサーチベースの質問生成）
- **[claude-skill-meta-skill](./claude-skill-meta-skill)**: Claude Codeで新しいスキルを作成するメタスキル（skill-creator）の研究と実装。スキル構造、設計パターン、ベストプラクティスを体系化。
- **[github-actions-cross-repo](./github-actions-cross-repo)**: GitHub Actionsで他のリポジトリを参照する方法の調査と検証。Deploy Keys、GitHub App、PATなど複数の認証方法を比較。
- **[japanese-to-romaji](./japanese-to-romaji)**: 日本語（漢字含む）→ローマ字変換ライブラリの比較研究：pykakasi、cutlet、romkan、jaconvを機能・精度・パフォーマンスで評価
- **[multi-agent-coordinator](./multi-agent-coordinator)**: Claude Codeフック+Skillsベースの軽量マルチエージェント調整システム（非侵襲的、透過的ファイルロック、Gitネイティブ、Beads並行編集戦略の分析と応用）
- **[multi-agent-maildeck](./multi-agent-maildeck)**: MailDeck: 非侵襲な多エージェント制御層（Beads + MCP Agent Mail + Claude Hooks）構想と実装ExecPlan。
- **[pdf-to-png-conversion](./pdf-to-png-conversion)**: PDF to PNG変換方法の比較検証。PyMuPDFが最速（0.116秒）、Ghostscriptが最小サイズ（15.1KB/ページ）。総合的にはPyMuPDFを推奨。
- **[prompt-ops-research](./prompt-ops-research)**: プロンプト自動改善とPromptOpsの包括的調査: Claude Code公式機能、コミュニティツール、主要フレームワーク（DSPy、AutoPrompt、LangSmith）の実践的活用法
- **[rails-json-params-handling](./rails-json-params-handling)**: RailsでContent-Type: application/jsonのパラメータは型を保持し、文字列に変換されない
- **[vibe-kanban-container-setup](./vibe-kanban-container-setup)**: vibe-kanban（AIエージェントオーケストレーター）を隔離されたコンテナ環境で安全に実行するための包括的なガイドと実装例。vibe-kanbanはnpx経由でエージェントCLIをコンテナ内で自動実行。ユーザーはAPI keyのみ必要でエージェントのインストールは不要。
<!-- [[[end]]] -->

## 使い方

### 新しい研究プロジェクトの作成

1. プロジェクト名のディレクトリを作成
2. そのディレクトリ内でコードと実験を実行
3. README.mdにプロジェクトの概要を記述
4. オプション：`_summary.md`を作成して一行サマリーを記述（自動生成を避ける場合）

### 注意事項

- このリポジトリの内容はAIによって生成されています
- 実用に使用する前に、人間による詳細なレビューが必要です
- 実験的なコードであり、本番環境での使用は推奨されません

## 自動化

GitHub Actionsを使用してREADMEを自動更新します。新しいプロジェクトが追加されると、ワークフローが自動的にプロジェクト一覧を更新します。

## ライセンス

このリポジトリのコンテンツはLICENSEファイルに従います。
