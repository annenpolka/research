# TaskChute 研究・仕様調査プロジェクト

## 概要

このプロジェクトは、日本発の時間管理・タスク管理ツール「TaskChute」の機能と仕様を調査し、再現実装に必要な仕様をまとめたものです。

## TaskChuteとは

TaskChuteは15年以上の歴史を持つ日本のタスク管理手法で、最新版の「TaskChute Cloud 2」は2024年8月にリリースされました。

### 主な特徴

- **時間を軸としたタスク管理**: 単なるTodoリストではなく、時間見積もりと実績記録を重視
- **ボトムアップアプローチ**: 理想的な計画ではなく、実際のログから現実的な計画を立てる
- **先送り0の実現**: 実行可能な計画により、タスクの先送りを防ぐ
- **3つの柱**: Plan（計画）、Log（記録）、Routine（ルーチン）

## プロジェクト構成

### SPECIFICATION.md

TaskChuteの詳細な仕様書です。以下の内容を含みます：

1. **概要と設計思想**
   - ボトムアップアプローチ
   - 現在への集中
   - 先送り0の実現

2. **コアコンセプト**
   - Plan（計画）: 実現可能なタスクリスト
   - Log（記録）: 詳細な時間記録
   - Routine（ルーチン）: 繰り返しタスクの自動化

3. **データ構造**
   - Task（タスク）
   - Routine（ルーチン）
   - Project（プロジェクト）
   - Mode（モード）
   - Tag（タグ）
   - Section（セクション）

4. **主要機能**
   - タスク管理（作成、実行、一覧）
   - ルーチン管理
   - ログ・振り返り
   - ビュー管理
   - キーボードショートカット

5. **技術仕様**
   - プラットフォーム要件
   - データ永続化
   - エクスポート形式
   - 外部連携

6. **実装ガイド**
   - 優先順位別のフェーズ分け
   - 実装のヒント
   - 考慮すべき制約事項

## 調査方法

以下の情報源から調査を実施しました：

### 公式ソース
- [TaskChute Cloud 2 公式サイト](https://www.taskchute.cloud/)
- [TaskChute Cloud ヘルプ](https://taskchute.cloud/pages/help)
- [タスクシュート協会公式ブログ](https://blog.taskchute.cloud/)

### 解説記事
- [TaskChute Cloud2完全ガイド](https://techgym.jp/column/taskchute-cloud2/)
- 開発者jMatsuzaki氏の[note記事](https://note.com/jmatsuzaki/n/n41f192c8552b)

### 関連ツール
- [Taskuma（たすくま）](https://apps.apple.com/jp/app/taskuma-taskchute-for-iphone/id896335635) - iPhone版TaskChute

## 主要な発見

### 1. 時間管理の仕組み

TaskChuteの核心は「時間の可視化」です：

- タスクに見積時間を設定
- 開始・終了時刻を記録
- 残り時間をリアルタイム表示
- 1日の予定終了時刻を自動計算
- 見積と実績の差分を分析

### 2. ルーチン機能の重要性

繰り返しタスクを自動生成することで：

- 毎日のタスク登録作業を削減
- 習慣化をサポート
- 柔軟な調整が可能（固定的ではない）

### 3. ログからの学習

過去のデータから：

- タスクの平均実行時間を算出
- 見積精度を向上
- 時間の使い方を振り返り

### 4. 分類システム

3つの分類軸を提供：

- **Project**: 大きな括り（「仕事」「ブログ」など）
- **Mode**: 活動の性質（「作成」「レビュー」など）
- **Tag**: 具体的なトピック（「Python」「緊急」など）

### 5. データのポータビリティ

- CSV形式でのエクスポート
- 外部サービス連携（Evernote、Googleカレンダー）
- 期間指定でのログ取得

## 再現実装の推奨フェーズ

### フェーズ1: MVP
- タスクの基本CRUD
- 時間記録機能
- 残り時間表示

### フェーズ2: コア機能
- プロジェクト・モード・タグ
- ルーチン機能
- ノート機能

### フェーズ3: 高度な機能
- CSVエクスポート
- カレンダー表示
- 統計・分析

### フェーズ4: UX向上
- カスタムビュー
- キーボードショートカット
- 外部連携

## 技術スタック候補

仕様調査から推奨される技術スタック：

### フロントエンド
- React/Vue/Svelte（コンポーネントベース）
- TypeScript（型安全性）
- TailwindCSS（スタイリング）
- React DnD（ドラッグ&ドロップ）

### バックエンド
- Node.js + Express
- Firebase（リアルタイム同期）
- PostgreSQL/MySQL（リレーショナルデータ）

### その他
- PWA対応（オフライン機能）
- WebSocket（リアルタイム更新）
- marked.js（Markdown）

## 重要な設計原則

TaskChuteを再現実装する際に守るべき原則：

1. **シンプルさを保つ**: 機能は豊富だが、UIはシンプルに
2. **時間を中心に**: すべての機能は時間管理を支援する
3. **現実主義**: 理想的な計画ではなく、実行可能な計画
4. **柔軟性**: ルーチンも分類も固定的ではなく調整可能
5. **継続的改善**: ログから学び、精度を向上

## 参考文献・情報源

- [TaskChute Cloud 2 公式サイト](https://www.taskchute.cloud/index.html)
- [TaskChute Cloud2完全ガイド](https://techgym.jp/column/taskchute-cloud2/)
- [jMatsuzaki氏の開発note](https://note.com/jmatsuzaki/n/n41f192c8552b)
- [TaskChute Cloud 初級編ステップ](https://blog.taskchute.cloud/beginner-step/)
- [Taskuma（たすくま）App Store](https://apps.apple.com/jp/app/taskuma-taskchute-for-iphone/id896335635)
- [プロジェクト・モード・タグの使い方](https://blog.taskchute.cloud/taskchute-cloud-2-projects-modes-and-tags/)
- [TaskChute Cloud 2 ヘルプページ](https://blog.taskchute.cloud/taskchute-cloud-2-help/)

## 結論

TaskChuteは単なるタスク管理ツールではなく、「時間の使い方を変える」ための包括的なシステムです。再現実装する際は、この時間管理の哲学を理解し、ユーザーが「今この瞬間に集中」できるような設計を心がけることが重要です。

## ライセンスと注意事項

このドキュメントは、公開されている情報を基に作成した調査資料です。TaskChute、TaskChute Cloud、TaskChute Cloud 2は、それぞれの開発者・運営者の商標および著作物です。

本仕様書は教育・研究目的で作成されており、実装する際は独自の実装とし、オリジナルの商標やブランドを侵害しないよう注意してください。
