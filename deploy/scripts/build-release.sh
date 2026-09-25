#!/usr/bin/env bash
# 本地构建发布包（在开发机执行，避免在服务器上 npm build 占满 CPU）
# 用法: bash deploy/scripts/build-release.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/deploy/release"
ENV_FILE="$ROOT/deploy/env/frontend-build.env"

mkdir -p "$OUT"
rm -f "$OUT"/*.tar.gz

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
else
  echo "[warn] 未找到 $ENV_FILE，使用默认 /api 与 localhost 域名"
  ADMIN_DOMAIN="${ADMIN_DOMAIN:-http://localhost:5173}"
  SELLER_DOMAIN="${SELLER_DOMAIN:-http://localhost:5175}"
  CUSTOMER_DOMAIN="${CUSTOMER_DOMAIN:-http://localhost:5174}"
fi

export VITE_API_BASE_URL=/api
unset VITE_API_ORIGIN
export VITE_API_ORIGIN=

build_app() {
  local name="$1"
  local dir="$2"
  shift 2
  echo "==> 构建 $name ..."
  cd "$dir"
  if [[ -x node_modules/.bin/vite ]]; then
    echo "  deps OK, skip npm install"
  else
    npm install
  fi
  env "$@" npm run build
  [[ -f dist/index.html ]] || { echo "错误: $dir/dist/index.html 不存在"; exit 1; }
  cd "$ROOT"
}

build_app admin "$ROOT/admin"
build_app seller "$ROOT/seller"
build_app customer "$ROOT/customer" \
  VITE_SELLER_URL="${SELLER_DOMAIN}" \
  VITE_BAIDU_MAP_AK="${VITE_BAIDU_MAP_AK:-}"

echo "==> 打包前端 dist ..."
tar -czf "$OUT/adminDist.tar.gz" -C "$ROOT/admin/dist" .
tar -czf "$OUT/sellerDist.tar.gz" -C "$ROOT/seller/dist" .
tar -czf "$OUT/customerDist.tar.gz" -C "$ROOT/customer/dist" .

echo "==> 打包后端 adminAPI（不含 venv / 数据库 / 媒体）..."
tar -czf "$OUT/backend.tar.gz" \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='db.sqlite3' \
  --exclude='.env' \
  --exclude='media' \
  --exclude='staticfiles' \
  -C "$ROOT" adminAPI

echo "==> 打包 deploy 脚本与 cron 配置 ..."
tar -czf "$OUT/deploy.tar.gz" \
  --exclude='release' \
  --exclude='env/frontend-build.env' \
  -C "$ROOT" deploy

echo ""
echo "发布包已生成: $OUT"
ls -lh "$OUT"/*.tar.gz
echo ""
echo "上传到服务器示例:"
echo "  scp deploy/release/*.tar.gz root@your-server:/var/www/admin/"
