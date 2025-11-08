# トラブルシューティングガイド

GitHub Actionsで他のリポジトリをチェックアウトする際によくある問題と解決方法をまとめています。

## 目次

1. [認証エラー](#認証エラー)
2. [パスの問題](#パスの問題)
3. [権限エラー](#権限エラー)
4. [パフォーマンスの問題](#パフォーマンスの問題)
5. [その他の問題](#その他の問題)

---

## 認証エラー

### エラー: "fatal: could not read Username for 'https://github.com'"

**原因**: プライベートリポジトリにアクセスする際、認証トークンが提供されていない

**解決方法**:

```yaml
# ❌ 間違い
- uses: actions/checkout@v4
  with:
    repository: owner/private-repo
    path: repo

# ✅ 正しい
- uses: actions/checkout@v4
  with:
    repository: owner/private-repo
    token: ${{ secrets.GH_PAT }}
    path: repo
```

### エラー: "Resource not accessible by integration"

**原因**: デフォルトの `GITHUB_TOKEN` は現在のリポジトリにのみアクセス可能

**解決方法**:

```yaml
# ❌ 間違い
- uses: actions/checkout@v4
  with:
    repository: owner/other-repo
    token: ${{ secrets.GITHUB_TOKEN }}

# ✅ 正しい
- uses: actions/checkout@v4
  with:
    repository: owner/other-repo
    token: ${{ secrets.GH_PAT }}
```

**PATの作成手順**:
1. GitHub Settings → Developer settings → Personal access tokens
2. "Generate new token" をクリック
3. `repo` スコープを選択
4. リポジトリのSecretsに追加

### エラー: "Bad credentials"

**原因**: トークンが無効、期限切れ、または権限不足

**チェックリスト**:
- [ ] トークンが正しくコピーされているか
- [ ] トークンの有効期限が切れていないか
- [ ] 必要なスコープ（`repo`）が付与されているか
- [ ] Secretが正しく設定されているか

**解決方法**:
1. 新しいPATを生成
2. リポジトリのSecretsを更新
3. ワークフローを再実行

---

## パスの問題

### エラー: "destination path already exists"

**原因**: 同じパスに複数回チェックアウトしようとしている

**解決方法**:

```yaml
# ❌ 間違い
- uses: actions/checkout@v4
- uses: actions/checkout@v4
  with:
    repository: owner/other-repo

# ✅ 正しい
- uses: actions/checkout@v4
  with:
    path: main
- uses: actions/checkout@v4
  with:
    repository: owner/other-repo
    path: other
```

### 問題: ファイルが見つからない

**原因**: パスの指定ミス

**デバッグ方法**:

```yaml
- name: Debug - Show directory structure
  run: |
    echo "Current directory:"
    pwd
    echo "Directory contents:"
    ls -la
    echo "Full structure:"
    find . -type d -maxdepth 3
```

**解決例**:

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    path: my-repo

- name: Use files from checked out repo
  run: |
    # ❌ 間違い - パスを指定していない
    cat README.md

    # ✅ 正しい
    cat my-repo/README.md
```

### 問題: サブディレクトリのみチェックアウトしたい

**解決方法**: `sparse-checkout` を使用

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    sparse-checkout: |
      docs/
      config/
    path: repo
```

---

## 権限エラー

### エラー: "refusing to allow a GitHub App to create or update workflow"

**原因**: GitHub Appのトークンでワークフローファイルを変更しようとしている

**解決方法**:

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    token: ${{ secrets.GH_PAT }}  # PATを使用
    path: repo
```

### エラー: "Resource not found"

**原因**: リポジトリが存在しない、または名前が間違っている

**チェックリスト**:
- [ ] リポジトリ名が正しいか（`owner/repo` 形式）
- [ ] リポジトリが実際に存在するか
- [ ] Organizationの場合、Organization名が正しいか
- [ ] リポジトリがアーカイブされていないか

**確認方法**:

```bash
# リポジトリの存在確認
curl https://api.github.com/repos/owner/repo

# 認証付きで確認
curl -H "Authorization: token YOUR_PAT" \
  https://api.github.com/repos/owner/private-repo
```

---

## パフォーマンスの問題

### 問題: チェックアウトに時間がかかる

**原因**: リポジトリが大きい、または履歴が長い

**解決方法1**: 履歴の深さを制限

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/large-repo
    token: ${{ secrets.GH_PAT }}
    path: repo
    fetch-depth: 1  # 最新のコミットのみ
```

**解決方法2**: サブモジュールをスキップ

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    token: ${{ secrets.GH_PAT }}
    path: repo
    submodules: false
```

**解決方法3**: LFSをスキップ

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    token: ${{ secrets.GH_PAT }}
    path: repo
    lfs: false
```

### 問題: 同じリポジトリを何度もチェックアウトしている

**解決方法**: キャッシュを使用

```yaml
- name: Cache external repository
  uses: actions/cache@v4
  id: cache-repo
  with:
    path: external-repo
    key: external-repo-${{ hashFiles('external-repo/.git/HEAD') }}

- name: Checkout if not cached
  if: steps.cache-repo.outputs.cache-hit != 'true'
  uses: actions/checkout@v4
  with:
    repository: owner/external-repo
    token: ${{ secrets.GH_PAT }}
    path: external-repo
```

---

## その他の問題

### 問題: 特定のブランチが見つからない

**エラー**: "fatal: Remote branch not found"

**解決方法**:

```yaml
# ブランチ名を確認
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    ref: main  # または master, develop など
    token: ${{ secrets.GH_PAT }}
    path: repo

# タグを使用
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    ref: v1.2.3
    token: ${{ secrets.GH_PAT }}
    path: repo

# コミットハッシュを使用
- uses: actions/checkout@v4
  with:
    repository: owner/repo
    ref: abc123def456
    token: ${{ secrets.GH_PAT }}
    path: repo
```

### 問題: ワークフローがトリガーされない

**原因**: チェックアウトしたリポジトリでの変更はワークフローをトリガーしない

**解決方法**: `repository_dispatch` イベントを使用

```yaml
# リポジトリA: 変更を通知
- name: Trigger workflow in another repo
  run: |
    curl -X POST \
      -H "Authorization: token ${{ secrets.GH_PAT }}" \
      -H "Accept: application/vnd.github.v3+json" \
      https://api.github.com/repos/owner/repo-b/dispatches \
      -d '{"event_type":"external_update"}'

# リポジトリB: イベントを受け取る
on:
  repository_dispatch:
    types: [external_update]
```

### 問題: プライベートリポジトリのアクションを使用できない

**エラー**: "Error: Unable to resolve action"

**解決方法**: リポジトリをチェックアウトして、ローカルアクションとして使用

```yaml
- uses: actions/checkout@v4
  with:
    repository: owner/private-action-repo
    token: ${{ secrets.GH_PAT }}
    path: .github/actions/private-action

- uses: ./.github/actions/private-action
```

### 問題: デバッグしたい

**デバッグステップを追加**:

```yaml
- name: Debug Information
  run: |
    echo "=== Environment ==="
    echo "Working directory: $(pwd)"
    echo "GitHub workspace: $GITHUB_WORKSPACE"
    echo "Runner temp: $RUNNER_TEMP"
    echo ""

    echo "=== Directory Structure ==="
    ls -la
    echo ""

    echo "=== Git Information ==="
    git --version
    git remote -v || echo "Not a git repository"
    echo ""

    echo "=== Disk Usage ==="
    df -h
```

**詳細ログを有効化**:

リポジトリのSecretsに追加:
- `ACTIONS_STEP_DEBUG`: `true`
- `ACTIONS_RUNNER_DEBUG`: `true`

---

## よくある質問

### Q: 同じOrganization内のリポジトリでもPATが必要？

A: はい。デフォルトの `GITHUB_TOKEN` は現在のリポジトリにのみアクセス可能です。

### Q: Forkしたリポジトリにアクセスできる？

A: 可能ですが、Fork元ではなくFork先のリポジトリ名を指定してください。

```yaml
- uses: actions/checkout@v4
  with:
    repository: your-username/forked-repo  # Fork先
    token: ${{ secrets.GH_PAT }}
```

### Q: サブモジュールとの違いは？

A: Git submodulesは `.gitmodules` ファイルで管理され、git cloneで自動取得されます。
GitHub Actionsのチェックアウトは、ワークフロー実行時のみ一時的に取得します。

### Q: 複数のOrganizationのリポジトリにアクセスしたい

A: PATを使用する場合、トークンに全Organizationへのアクセス権が必要です。
GitHub Appを使用する場合は、各Organizationでアプリをインストールしてください。

---

## さらなるサポート

問題が解決しない場合:

1. [GitHub Community Discussions](https://github.com/orgs/community/discussions)で質問
2. [actions/checkout Issues](https://github.com/actions/checkout/issues)を検索
3. GitHub Supportに連絡

デバッグ情報を提供する際は:
- ワークフローファイルの関連部分
- エラーメッセージの全文
- デバッグログ（機密情報を除く）
