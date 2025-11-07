#!/bin/bash
# vibe-kanbanをKubernetesで実行するスクリプト

set -e

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== vibe-kanban Kubernetes実行スクリプト ===${NC}\n"

# Kubernetesの動作確認
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}エラー: kubectlが見つかりません${NC}"
    echo "kubectlをインストールしてください: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# オプション解析
MODE="${1:-deploy}"
NAMESPACE="${2:-default}"

case "$MODE" in
  deploy)
    echo -e "${YELLOW}vibe-kanbanをKubernetesにデプロイします${NC}"
    echo "ネームスペース: $NAMESPACE"

    # ネームスペースの作成（存在しない場合）
    kubectl get namespace "$NAMESPACE" &>/dev/null || \
      kubectl create namespace "$NAMESPACE"

    echo -e "\n${YELLOW}ConfigMapとSecretを作成中...${NC}"
    kubectl apply -f kubernetes/configmap.yaml -n "$NAMESPACE"

    echo -e "\n${YELLOW}Deploymentを作成中...${NC}"
    kubectl apply -f kubernetes/deployment.yaml -n "$NAMESPACE"

    echo -e "\n${YELLOW}Serviceを作成中...${NC}"
    kubectl apply -f kubernetes/service.yaml -n "$NAMESPACE"

    echo -e "\n${YELLOW}NetworkPolicyを作成中...${NC}"
    kubectl apply -f kubernetes/networkpolicy.yaml -n "$NAMESPACE"

    echo -e "\n${GREEN}✓ vibe-kanbanのデプロイが完了しました！${NC}"

    echo -e "\n${YELLOW}デプロイステータスを確認中...${NC}"
    kubectl rollout status deployment/vibe-kanban -n "$NAMESPACE"

    echo -e "\n${YELLOW}Podの状態:${NC}"
    kubectl get pods -l app=vibe-kanban -n "$NAMESPACE"

    echo -e "\n${YELLOW}アクセス方法:${NC}"
    echo "1. Port-forward: kubectl port-forward -n $NAMESPACE svc/vibe-kanban 3000:80"
    echo "2. Ingress経由: 設定されている場合は、Ingressのホスト名でアクセス"
    ;;

  delete)
    echo -e "${YELLOW}vibe-kanbanを削除します${NC}"
    echo "ネームスペース: $NAMESPACE"

    kubectl delete -f kubernetes/networkpolicy.yaml -n "$NAMESPACE" 2>/dev/null || true
    kubectl delete -f kubernetes/service.yaml -n "$NAMESPACE" 2>/dev/null || true
    kubectl delete -f kubernetes/deployment.yaml -n "$NAMESPACE" 2>/dev/null || true
    kubectl delete -f kubernetes/configmap.yaml -n "$NAMESPACE" 2>/dev/null || true

    echo -e "\n${GREEN}✓ vibe-kanbanを削除しました${NC}"
    ;;

  status)
    echo -e "${YELLOW}vibe-kanbanの状態を確認します${NC}"
    echo "ネームスペース: $NAMESPACE"
    echo ""

    echo -e "${YELLOW}Deployment:${NC}"
    kubectl get deployment vibe-kanban -n "$NAMESPACE" 2>/dev/null || echo "見つかりません"
    echo ""

    echo -e "${YELLOW}Pods:${NC}"
    kubectl get pods -l app=vibe-kanban -n "$NAMESPACE" 2>/dev/null || echo "見つかりません"
    echo ""

    echo -e "${YELLOW}Service:${NC}"
    kubectl get service vibe-kanban -n "$NAMESPACE" 2>/dev/null || echo "見つかりません"
    echo ""

    echo -e "${YELLOW}Ingress:${NC}"
    kubectl get ingress vibe-kanban-ingress -n "$NAMESPACE" 2>/dev/null || echo "見つかりません"
    ;;

  logs)
    echo -e "${YELLOW}vibe-kanbanのログを表示します${NC}"
    echo "ネームスペース: $NAMESPACE"

    POD=$(kubectl get pods -l app=vibe-kanban -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$POD" ]; then
      echo -e "${RED}エラー: Podが見つかりません${NC}"
      exit 1
    fi

    echo -e "\nPod: $POD\n"
    kubectl logs -f "$POD" -n "$NAMESPACE"
    ;;

  port-forward)
    echo -e "${YELLOW}Port-forwardを設定します${NC}"
    echo "ネームスペース: $NAMESPACE"

    PORT="${3:-3000}"
    echo "ローカルポート: $PORT"
    echo -e "\n${GREEN}アクセスURL: http://localhost:$PORT${NC}\n"

    kubectl port-forward -n "$NAMESPACE" svc/vibe-kanban "$PORT":80
    ;;

  scale)
    REPLICAS="${3:-1}"
    echo -e "${YELLOW}vibe-kanbanをスケールします${NC}"
    echo "ネームスペース: $NAMESPACE"
    echo "レプリカ数: $REPLICAS"

    kubectl scale deployment/vibe-kanban --replicas="$REPLICAS" -n "$NAMESPACE"

    echo -e "\n${GREEN}✓ スケール完了${NC}"
    kubectl get deployment vibe-kanban -n "$NAMESPACE"
    ;;

  restart)
    echo -e "${YELLOW}vibe-kanbanを再起動します${NC}"
    echo "ネームスペース: $NAMESPACE"

    kubectl rollout restart deployment/vibe-kanban -n "$NAMESPACE"
    kubectl rollout status deployment/vibe-kanban -n "$NAMESPACE"

    echo -e "\n${GREEN}✓ 再起動完了${NC}"
    ;;

  describe)
    echo -e "${YELLOW}vibe-kanbanの詳細情報を表示します${NC}"
    echo "ネームスペース: $NAMESPACE"
    echo ""

    POD=$(kubectl get pods -l app=vibe-kanban -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$POD" ]; then
      echo -e "${RED}エラー: Podが見つかりません${NC}"
      exit 1
    fi

    kubectl describe pod "$POD" -n "$NAMESPACE"
    ;;

  events)
    echo -e "${YELLOW}vibe-kanban関連のイベントを表示します${NC}"
    echo "ネームスペース: $NAMESPACE"
    echo ""

    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | grep vibe-kanban || echo "イベントなし"
    ;;

  *)
    echo -e "${RED}エラー: 不明なモード '$MODE'${NC}\n"
    echo "使用方法: $0 [mode] [namespace] [options]"
    echo ""
    echo "利用可能なモード:"
    echo "  deploy        - vibe-kanbanをデプロイ（デフォルト）"
    echo "  delete        - vibe-kanbanを削除"
    echo "  status        - 状態を確認"
    echo "  logs          - ログを表示"
    echo "  port-forward  - Port-forwardを設定"
    echo "  scale         - レプリカ数を変更"
    echo "  restart       - 再起動"
    echo "  describe      - 詳細情報を表示"
    echo "  events        - イベントを表示"
    echo ""
    echo "例:"
    echo "  $0 deploy default"
    echo "  $0 port-forward default 8080"
    echo "  $0 scale default 3"
    exit 1
    ;;
esac
