#!/usr/bin/env bash
# 服务器端：解压 backend.tar.gz 并创建虚拟环境（在 /var/www/admin 下执行）
# 用法: bash server-install-backend.sh [/var/www/admin/backend.tar.gz]
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/var/www/admin}"
BACKEND_DIR="$DEPLOY_ROOT/backend"
ARCHIVE="${1:-$DEPLOY_ROOT/backend.tar.gz}"
PYTHON="${PYTHON:-python3}"
SERVICE_NAME="${SERVICE_NAME:-ecommerce-backend}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -f "$ARCHIVE" ]]; then
  echo "错误: 找不到压缩包 $ARCHIVE"
  echo "请先将 backend.tar.gz 上传到 $DEPLOY_ROOT/"
  exit 1
fi

echo "==> 部署后端到 $BACKEND_DIR"
mkdir -p "$BACKEND_DIR"
# 保留 .env / media / db.sqlite3
if [[ -f "$BACKEND_DIR/.env" ]]; then
  cp "$BACKEND_DIR/.env" "/tmp/ecommerce-backend.env.bak"
fi
if [[ -d "$BACKEND_DIR/media" ]]; then
  rm -rf "/tmp/ecommerce-media.bak"
  cp -a "$BACKEND_DIR/media" "/tmp/ecommerce-media.bak"
fi
if [[ -f "$BACKEND_DIR/db.sqlite3" ]]; then
  cp "$BACKEND_DIR/db.sqlite3" "/tmp/ecommerce-db.sqlite3.bak"
fi

# 清空代码目录（保留 venv 由下方重建或复用）
find "$BACKEND_DIR" -mindepth 1 -maxdepth 1 ! -name 'venv' ! -name '.venv' -exec rm -rf {} +

tar -xzf "$ARCHIVE" -C "$BACKEND_DIR" --strip-components=1

if [[ -f "/tmp/ecommerce-backend.env.bak" ]]; then
  mv "/tmp/ecommerce-backend.env.bak" "$BACKEND_DIR/.env"
elif [[ ! -f "$BACKEND_DIR/.env" ]]; then
  echo "[warn] 未找到 .env，请复制 deploy/env/backend.env.example 到 $BACKEND_DIR/.env"
fi
if [[ -d "/tmp/ecommerce-media.bak" ]]; then
  rm -rf "$BACKEND_DIR/media"
  mv "/tmp/ecommerce-media.bak" "$BACKEND_DIR/media"
fi
if [[ -f "/tmp/ecommerce-db.sqlite3.bak" ]]; then
  mv "/tmp/ecommerce-db.sqlite3.bak" "$BACKEND_DIR/db.sqlite3"
fi

if [[ ! -d "$BACKEND_DIR/venv" ]]; then
  echo "==> 创建虚拟环境 ..."
  "$PYTHON" -m venv "$BACKEND_DIR/venv"
fi

# shellcheck disable=SC1091
source "$BACKEND_DIR/venv/bin/activate"
pip install -U pip wheel
pip install -r "$BACKEND_DIR/requirements.txt"

echo "==> migrate & collectstatic ..."
cd "$BACKEND_DIR"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "==> verify order API routes ..."
python manage.py shell -c "from django.urls import reverse; print('confirm-receipt route:', reverse('order-confirm-receipt', args=[1]))"

echo "==> sync sidebar menus ..."
python manage.py sync_menus

echo "==> init demo data (first deploy) ..."
if python manage.py shell -c "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(username='admin').exists() else 1)"; then
  echo "  admin exists, skip init_data (run: python manage.py init_data to reset demo)"
else
  python manage.py init_data
fi

if [[ -f "$DEPLOY_ROOT/deploy/systemd/ecommerce-backend.service" ]]; then
  cp "$DEPLOY_ROOT/deploy/systemd/ecommerce-backend.service" "/etc/systemd/system/${SERVICE_NAME}.service"
elif [[ -f "$(dirname "$0")/../systemd/ecommerce-backend.service" ]]; then
  cp "$(dirname "$0")/../systemd/ecommerce-backend.service" "/etc/systemd/system/${SERVICE_NAME}.service"
fi

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# 按 .env 中 BACKEND_PORT 同步 Nginx 反代
if [[ -f "$SCRIPT_DIR/sync-backend-port.sh" ]]; then
  DEPLOY_ROOT="$DEPLOY_ROOT" bash "$SCRIPT_DIR/sync-backend-port.sh"
elif [[ -f "$DEPLOY_ROOT/deploy/scripts/sync-backend-port.sh" ]]; then
  DEPLOY_ROOT="$DEPLOY_ROOT" bash "$DEPLOY_ROOT/deploy/scripts/sync-backend-port.sh"
fi

systemctl restart "$SERVICE_NAME"
systemctl --no-pager status "$SERVICE_NAME" || true

install_scheduled_tasks() {
  local cron_src="$DEPLOY_ROOT/deploy/cron/ecommerce-backend.crontab"
  local task_sh="$DEPLOY_ROOT/deploy/scripts/run-scheduled-tasks.sh"
  if [[ ! -f "$cron_src" || ! -f "$task_sh" ]]; then
    echo "[warn] 未找到 cron 配置（$cron_src），请上传 deploy.tar.gz 后重跑本脚本"
    return 0
  fi
  mkdir -p /var/log/ecommerce
  chmod +x "$task_sh"
  install -m 644 "$cron_src" /etc/cron.d/ecommerce-backend
  echo "==> cron 已安装: /etc/cron.d/ecommerce-backend"
}

install_scheduled_tasks

echo ""
echo "后端部署完成。日志: journalctl -u $SERVICE_NAME -f"
