#!/usr/bin/env bash
# 检查 Nginx 配置与 Cloudflare 隧道部署（源站无需 SSL）
# 用法: bash deploy/scripts/server-check-nginx.sh
set -euo pipefail

NGINX_ROOT="${NGINX_ROOT:-/opt/config/nginx}"
CONF_D="$NGINX_ROOT/conf.d"

echo "========== 架构说明 =========="
echo "Nginx 在容器内，include /etc/nginx/conf.d 为容器路径"
echo "宿主机 $CONF_D 通常 volume 挂载到容器 /etc/nginx/conf.d"
echo "HTTPS 由 Cloudflare 隧道终结，源站只需 listen 80"

echo ""
echo "========== conf.d 电商站点 =========="
if [[ -d "$CONF_D" ]]; then
  for f in 08-ecommerce-admin.conf 09-ecommerce-seller.conf 10-ecommerce-customer.conf; do
    if [[ -f "$CONF_D/$f" ]]; then
      echo "[已安装] $f"
      grep -E 'listen|server_name|proxy_pass|X-Forwarded-Proto' "$CONF_D/$f" | head -8
    else
      echo "[未安装] $f"
    fi
  done
else
  echo "目录不存在: $CONF_D"
fi

echo ""
echo "========== 建议 =========="
echo "1. 勿在 Nginx 配置 ssl_certificate / listen 443"
echo "2. backend/.env 与 frontend-build.env 使用 https:// 公网域名"
echo "3. 容器内 reload: docker exec <nginx> nginx -t && docker exec <nginx> nginx -s reload"
echo "4. 参考 deploy/cloudflared/config.example.yml 配置隧道 ingress"
