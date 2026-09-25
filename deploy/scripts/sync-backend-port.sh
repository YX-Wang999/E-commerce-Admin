#!/usr/bin/env bash
# 从 backend/.env 读取 BACKEND_PORT / BACKEND_BIND，同步到 Nginx 反代与 systemd
# 用法: bash deploy/scripts/sync-backend-port.sh
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/var/www/admin}"
BACKEND_DIR="$DEPLOY_ROOT/backend"
NGINX_SRC="$DEPLOY_ROOT/deploy/nginx"
NGINX_DST="${NGINX_DST:-/opt/config/nginx/conf.d}"
SERVICE_NAME="${SERVICE_NAME:-ecommerce-backend}"

BACKEND_PORT=8002
BACKEND_BIND=127.0.0.1
BACKEND_UPSTREAM_HOST=127.0.0.1

if [[ -f "$BACKEND_DIR/.env" ]]; then
  while IFS='=' read -r key value; do
    key=$(echo "$key" | tr -d '\r' | xargs)
    value=$(echo "$value" | tr -d '\r' | xargs)
    case "$key" in
      BACKEND_PORT) BACKEND_PORT="$value" ;;
      BACKEND_BIND) BACKEND_BIND="$value" ;;
      BACKEND_UPSTREAM_HOST) BACKEND_UPSTREAM_HOST="$value" ;;
    esac
  done < <(grep -E '^(BACKEND_PORT|BACKEND_BIND|BACKEND_UPSTREAM_HOST)=' "$BACKEND_DIR/.env" || true)
fi

# Linux 原生 Docker 无 host.docker.internal；Nginx 容器需用宿主机网关 IP 访问 Daphne
resolve_nginx_upstream_host() {
  local host="$1"
  if [[ "$host" != "host.docker.internal" ]]; then
    echo "$host"
    return
  fi
  if command -v getent >/dev/null 2>&1 && getent hosts host.docker.internal >/dev/null 2>&1; then
    echo "host.docker.internal"
    return
  fi
  local docker_gw=""
  if command -v docker >/dev/null 2>&1; then
    docker_gw=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null || true)
  fi
  if [[ -n "$docker_gw" && "$docker_gw" != "null" ]]; then
    echo "$docker_gw"
    return
  fi
  echo "172.17.0.1"
}

BACKEND_UPSTREAM_HOST="$(resolve_nginx_upstream_host "$BACKEND_UPSTREAM_HOST")"
UPSTREAM="${BACKEND_UPSTREAM_HOST}:${BACKEND_PORT}"
echo "==> 后端 upstream: http://${UPSTREAM} (Daphne bind: ${BACKEND_BIND}:${BACKEND_PORT})"
if [[ "$BACKEND_UPSTREAM_HOST" != "127.0.0.1" && "$BACKEND_UPSTREAM_HOST" != "host.docker.internal" ]]; then
  echo "    (host.docker.internal 不可用，已改用 Docker 网桥网关 ${BACKEND_UPSTREAM_HOST})"
fi

copy_nginx() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  sed -E "s|proxy_pass http://[^/]+/|proxy_pass http://${UPSTREAM}/|g" "$src" > "$dst"
}

for f in 08-ecommerce-admin.conf 09-ecommerce-seller.conf 10-ecommerce-customer.conf; do
  if [[ -f "$NGINX_SRC/$f" ]]; then
    copy_nginx "$NGINX_SRC/$f" "$NGINX_DST/$f"
    echo "  已写入 $NGINX_DST/$f"
  fi
done

if [[ -f "$DEPLOY_ROOT/deploy/systemd/ecommerce-backend.service" ]]; then
  cp "$DEPLOY_ROOT/deploy/systemd/ecommerce-backend.service" "/etc/systemd/system/${SERVICE_NAME}.service"
  systemctl daemon-reload
  echo "  已更新 systemd ${SERVICE_NAME}.service"
fi

echo "完成。请执行:"
echo "  docker exec nginx nginx -t && docker exec nginx nginx -s reload"
echo "  systemctl restart ${SERVICE_NAME}"
