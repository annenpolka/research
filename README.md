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
- **[claude-auto-approve-commands](./claude-auto-approve-commands)**: Claude Codeで特定のコマンドを自動許可する設定方法の調査と実装（allowedTools、defaultMode、PreToolUseフック）
- **[claude-code-prompt-improver-analysis](./claude-code-prompt-improver-analysis)**: Claude Code Prompt Improver - 曖昧なプロンプトを自動改善するUserPromptSubmitフック（83行のPython、会話履歴活用、リサーチベースの質問生成）
- **[japanese-to-romaji](./japanese-to-romaji)**: 日本語（漢字含む）→ローマ字変換ライブラリの比較研究：pykakasi、cutlet、romkan、jaconvを機能・精度・パフォーマンスで評価
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
