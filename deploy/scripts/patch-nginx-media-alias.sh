#!/usr/bin/env bash
# 将三端 Nginx 的 /media/ 从 proxy_pass 改为 alias 直读磁盘（解决上传后 404）
# 用法: bash deploy/scripts/patch-nginx-media-alias.sh
set -euo pipefail

NGINX_DST="${NGINX_DST:-/opt/config/nginx/conf.d}"
MEDIA_ALIAS="${MEDIA_ALIAS:-/var/www/admin/backend/media/}"

MEDIA_BLOCK="    location /media/ {
        alias ${MEDIA_ALIAS};
        expires 7d;
        add_header Cache-Control \"public\";
        access_log off;
    }"

patch_file() {
  local name="$1"
  local path="$NGINX_DST/$name"
  [[ -f "$path" ]] || { echo "[skip] $path 不存在"; return 0; }
  python3 - "$path" "$MEDIA_BLOCK" <<'PY'
import re, sys
path, block = sys.argv[1], sys.argv[2]
text = open(path, encoding='utf-8').read()
new, n = re.subn(
    r'    location /media/ \{.*?\n    \}',
    block,
    text,
    count=1,
    flags=re.DOTALL,
)
if n == 0:
    if 'alias /var/www/admin/backend/media/' in text:
        print(f'[ok] {path} 已是 alias，跳过')
        sys.exit(0)
    raise SystemExit(f'[error] 未找到 location /media/ 块: {path}')
open(path, 'w', encoding='utf-8').write(new)
print(f'[patched] {path}')
PY
}

for f in 08-ecommerce-admin.conf 09-ecommerce-seller.conf 10-ecommerce-customer.conf; do
  patch_file "$f"
done

echo ""
echo "下一步:"
echo "  docker exec nginx nginx -t && docker exec nginx nginx -s reload"
echo "  curl -I -H 'Host: admin.wangyixiang.xyz' http://127.0.0.1/media/products/2026/06/某文件.png"
