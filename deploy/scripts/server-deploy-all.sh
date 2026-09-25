#!/usr/bin/env bash
# 服务器端一键部署（需 root）
# 将 deploy/release/*.tar.gz 与 deploy/ 目录一并上传到 /var/www/admin/ 后执行:
#   cd /var/www/admin && bash deploy/scripts/server-deploy-all.sh
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/var/www/admin}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -f "$DEPLOY_ROOT/deploy.tar.gz" ]]; then
  echo "========== 0/3 解压 deploy 脚本 =========="
  tar -xzf "$DEPLOY_ROOT/deploy.tar.gz" -C "$DEPLOY_ROOT"
fi

echo "========== 1/3 部署前端 =========="
bash "$SCRIPT_DIR/server-deploy-frontends.sh" "$DEPLOY_ROOT"

echo ""
echo "========== 2/3 部署后端 =========="
bash "$SCRIPT_DIR/server-install-backend.sh" "$DEPLOY_ROOT/backend.tar.gz"

echo ""
echo "========== 3/3 安装 Nginx 配置（挂载到容器 /etc/nginx/conf.d/）=========="
bash "$SCRIPT_DIR/sync-backend-port.sh"

echo ""
echo "全部完成。请检查:"
echo "  - 电商后端默认端口 8002（backend/.env 中 BACKEND_PORT 可改）"
echo "  - 配置已同步到 ${NGINX_DST:-/opt/config/nginx/conf.d/}（容器内 /etc/nginx/conf.d/）"
echo "  - docker exec <nginx> nginx -t && docker exec <nginx> nginx -s reload"
echo "  - systemctl status ecommerce-backend"
