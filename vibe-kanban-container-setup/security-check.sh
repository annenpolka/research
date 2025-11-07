#!/bin/bash
# vibe-kanbanコンテナのセキュリティチェックスクリプト

set -e

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== vibe-kanban セキュリティチェック ===${NC}\n"

# コンテナ名の取得
CONTAINER_NAME="${1:-vibe-kanban}"

# コンテナの存在確認
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}エラー: コンテナ '${CONTAINER_NAME}' が見つかりません${NC}"
    echo "使用方法: $0 [container-name]"
    exit 1
fi

# コンテナが実行中か確認
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}警告: コンテナ '${CONTAINER_NAME}' は停止しています${NC}"
fi

echo -e "${YELLOW}対象コンテナ: ${CONTAINER_NAME}${NC}\n"

# ===========================
# セキュリティチェック項目
# ===========================

check_passed=0
check_failed=0
check_warning=0

check_item() {
    local status=$1
    local message=$2

    case $status in
        pass)
            echo -e "${GREEN}✓${NC} $message"
            ((check_passed++))
            ;;
        fail)
            echo -e "${RED}✗${NC} $message"
            ((check_failed++))
            ;;
        warn)
            echo -e "${YELLOW}⚠${NC} $message"
            ((check_warning++))
            ;;
    esac
}

# 1. ユーザーチェック
echo -e "${BLUE}[1] ユーザー設定${NC}"
USER_INFO=$(docker inspect --format='{{.Config.User}}' "$CONTAINER_NAME")
if [ -z "$USER_INFO" ] || [ "$USER_INFO" = "0" ] || [ "$USER_INFO" = "root" ]; then
    check_item "fail" "rootユーザーで実行されています"
else
    check_item "pass" "非rootユーザーで実行されています (UID: $USER_INFO)"
fi
echo ""

# 2. ケーパビリティチェック
echo -e "${BLUE}[2] ケーパビリティ${NC}"
CAPS=$(docker inspect --format='{{.HostConfig.CapDrop}}' "$CONTAINER_NAME")
if echo "$CAPS" | grep -q "ALL"; then
    check_item "pass" "すべてのケーパビリティが削除されています"
else
    check_item "warn" "一部のケーパビリティが残っています: $CAPS"
fi
echo ""

# 3. 読み取り専用ファイルシステム
echo -e "${BLUE}[3] ファイルシステム${NC}"
READONLY=$(docker inspect --format='{{.HostConfig.ReadonlyRootfs}}' "$CONTAINER_NAME")
if [ "$READONLY" = "true" ]; then
    check_item "pass" "読み取り専用ファイルシステムが有効"
else
    check_item "warn" "ファイルシステムが書き込み可能"
fi
echo ""

# 4. セキュリティオプション
echo -e "${BLUE}[4] セキュリティオプション${NC}"
SECOPT=$(docker inspect --format='{{.HostConfig.SecurityOpt}}' "$CONTAINER_NAME")
if echo "$SECOPT" | grep -q "no-new-privileges:true"; then
    check_item "pass" "no-new-privileges が有効"
else
    check_item "warn" "no-new-privileges が無効"
fi

if echo "$SECOPT" | grep -q "apparmor"; then
    check_item "pass" "AppArmorプロファイルが適用されています"
elif echo "$SECOPT" | grep -q "selinux"; then
    check_item "pass" "SELinuxが適用されています"
else
    check_item "warn" "AppArmor/SELinuxが適用されていません"
fi
echo ""

# 5. リソース制限
echo -e "${BLUE}[5] リソース制限${NC}"
MEMORY=$(docker inspect --format='{{.HostConfig.Memory}}' "$CONTAINER_NAME")
if [ "$MEMORY" != "0" ]; then
    MEMORY_MB=$((MEMORY / 1024 / 1024))
    check_item "pass" "メモリ制限: ${MEMORY_MB}MB"
else
    check_item "warn" "メモリ制限が設定されていません"
fi

CPU=$(docker inspect --format='{{.HostConfig.NanoCpus}}' "$CONTAINER_NAME")
if [ "$CPU" != "0" ]; then
    CPU_CORES=$(echo "scale=2; $CPU / 1000000000" | bc)
    check_item "pass" "CPU制限: ${CPU_CORES}コア"
else
    check_item "warn" "CPU制限が設定されていません"
fi

PIDS=$(docker inspect --format='{{.HostConfig.PidsLimit}}' "$CONTAINER_NAME")
if [ "$PIDS" != "0" ] && [ -n "$PIDS" ]; then
    check_item "pass" "PID制限: ${PIDS}"
else
    check_item "warn" "PID制限が設定されていません"
fi
echo ""

# 6. ネットワークモード
echo -e "${BLUE}[6] ネットワーク${NC}"
NETWORK=$(docker inspect --format='{{.HostConfig.NetworkMode}}' "$CONTAINER_NAME")
if [ "$NETWORK" = "none" ]; then
    check_item "pass" "ネットワークが完全に隔離されています"
elif [ "$NETWORK" = "bridge" ]; then
    check_item "warn" "ブリッジネットワークを使用（外部アクセス可能）"
else
    check_item "warn" "ネットワークモード: $NETWORK"
fi
echo ""

# 7. ボリュームマウント
echo -e "${BLUE}[7] ボリュームマウント${NC}"
MOUNTS=$(docker inspect --format='{{range .Mounts}}{{.Type}}:{{.Source}}->{{.Destination}} {{end}}' "$CONTAINER_NAME")
if [ -z "$MOUNTS" ]; then
    check_item "pass" "ボリュームマウントなし"
else
    echo -e "${YELLOW}マウント一覧:${NC}"
    docker inspect --format='{{range .Mounts}}  {{.Type}}: {{.Source}} -> {{.Destination}} (RW:{{.RW}}){{"\n"}}{{end}}' "$CONTAINER_NAME"

    # 危険なマウントをチェック
    if echo "$MOUNTS" | grep -q "/var/run/docker.sock"; then
        check_item "fail" "Docker socketがマウントされています（危険）"
    elif echo "$MOUNTS" | grep -qE "/(etc|bin|usr|sys|proc)"; then
        check_item "fail" "システムディレクトリがマウントされています（危険）"
    else
        check_item "warn" "カスタムボリュームがマウントされています"
    fi
fi
echo ""

# 8. 権限昇格
echo -e "${BLUE}[8] 権限設定${NC}"
PRIVILEGED=$(docker inspect --format='{{.HostConfig.Privileged}}' "$CONTAINER_NAME")
if [ "$PRIVILEGED" = "true" ]; then
    check_item "fail" "特権モードで実行されています（危険）"
else
    check_item "pass" "特権モードではありません"
fi
echo ""

# 9. イメージスキャン（Trivyが利用可能な場合）
echo -e "${BLUE}[9] イメージ脆弱性スキャン${NC}"
if command -v trivy &> /dev/null; then
    IMAGE=$(docker inspect --format='{{.Config.Image}}' "$CONTAINER_NAME")
    echo -e "${YELLOW}Trivyでスキャン中...${NC}"
    trivy image --severity HIGH,CRITICAL "$IMAGE" --quiet --format table
else
    check_item "warn" "Trivyがインストールされていません（脆弱性スキャン不可）"
    echo "  インストール: https://aquasecurity.github.io/trivy/"
fi
echo ""

# 10. ランタイムチェック
echo -e "${BLUE}[10] ランタイム${NC}"
RUNTIME=$(docker inspect --format='{{.HostConfig.Runtime}}' "$CONTAINER_NAME")
if [ "$RUNTIME" = "runsc" ] || [ "$RUNTIME" = "gvisor" ]; then
    check_item "pass" "gVisorランタイムを使用（強固な隔離）"
elif [ -z "$RUNTIME" ] || [ "$RUNTIME" = "runc" ]; then
    check_item "warn" "標準ランタイム（runc）を使用"
else
    check_item "warn" "カスタムランタイム: $RUNTIME"
fi
echo ""

# ===========================
# 結果サマリー
# ===========================

echo -e "${BLUE}===========================${NC}"
echo -e "${BLUE}セキュリティチェック結果${NC}"
echo -e "${BLUE}===========================${NC}"
echo -e "${GREEN}合格: ${check_passed}${NC}"
echo -e "${YELLOW}警告: ${check_warning}${NC}"
echo -e "${RED}失敗: ${check_failed}${NC}"
echo ""

if [ $check_failed -eq 0 ] && [ $check_warning -eq 0 ]; then
    echo -e "${GREEN}✓ すべてのセキュリティチェックに合格しました！${NC}"
    exit 0
elif [ $check_failed -eq 0 ]; then
    echo -e "${YELLOW}⚠ 警告があります。可能であれば改善してください。${NC}"
    exit 0
else
    echo -e "${RED}✗ セキュリティ上の問題があります。修正が推奨されます。${NC}"
    exit 1
fi
