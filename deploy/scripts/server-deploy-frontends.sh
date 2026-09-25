#!/usr/bin/env bash
# 服务器端：解压三个前端 dist 包
# 用法: bash server-deploy-frontends.sh [/var/www/admin]
set -euo pipefail

DEPLOY_ROOT="${1:-/var/www/admin}"

deploy_dist() {
  local archive="$1"
  local target="$2"
  local name="$3"
  if [[ ! -f "$archive" ]]; then
    echo "[skip] 未找到 $name: $archive"
    return 0
  fi
  echo "==> 部署 $name -> $target"
  mkdir -p "$target"
  find "$target" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  tar -xzf "$archive" -C "$target"
}

deploy_dist "$DEPLOY_ROOT/adminDist.tar.gz" "$DEPLOY_ROOT/adminDist" "平台后台"
deploy_dist "$DEPLOY_ROOT/sellerDist.tar.gz" "$DEPLOY_ROOT/sellerDist" "商户后台"
deploy_dist "$DEPLOY_ROOT/customerDist.tar.gz" "$DEPLOY_ROOT/customerDist" "用户商城"

echo ""
echo "前端静态文件部署完成。"
echo "请确认 nginx conf.d 中 08/09/10 已配置并 reload。"
