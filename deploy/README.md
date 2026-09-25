# 部署说明

## 架构概览

```
用户浏览器 ──HTTPS──▶ Cloudflare 隧道 (cloudflared) ──HTTP──▶ Nginx 容器 :80
                                                              ├── 静态 admin/seller/customerDist
                                                              └── 反代 /api、/media、/ws ──▶ 宿主机 Daphne :8002（可配置）
```


| 层级     | 说明                                                                                   |
| ------ | ------------------------------------------------------------------------------------ |
| 公网     | **HTTPS** 由 Cloudflare 终结，无需在源站配置 `ssl_certificate`                                  |
| Nginx  | **容器内**运行，仅 `listen 80`；`nginx.conf` 的 `include /etc/nginx/conf.d/*.conf` 为**容器内路径** |
| 宿主机    | `/opt/config/nginx/conf.d/` 等目录通常通过 volume 挂载到容器 `/etc/nginx/conf.d/`                |
| 后端     | 宿主机 systemd（Daphne），默认 **8002**（`backend/.env` 中 `BACKEND_PORT`；8000/8001 留给其他服务）    |
| Django | `SECURE_PROXY_SSL_HEADER` 依赖 Nginx 转发 `X-Forwarded-Proto`（隧道会带入 `https`）             |




### 域名规划


| 站点   | 公网域名                               | Nginx 配置                     |
| ---- | ---------------------------------- | ---------------------------- |
| 平台后台 | `https://admin.wangyixiang.xyz`    | `08-ecommerce-admin.conf`    |
| 商户后台 | `https://seller.wangyixiang.xyz`   | `09-ecommerce-seller.conf`   |
| 用户商城 | `https://customer.wangyixiang.xyz` | `10-ecommerce-customer.conf` |


---



## 目录约定（宿主机）

```
/var/www/admin/
├── adminDist/          # 平台后台静态文件（需挂载进 Nginx 容器）
├── sellerDist/
├── customerDist/
├── backend/            # Django 后端 + venv（宿主机 systemd）
└── deploy/             # 脚本与 nginx 模板
```

Nginx 配置：复制 `deploy/nginx/08|09|10-*.conf` 到**挂载卷对应目录**（如宿主机 `/opt/config/nginx/conf.d/` → 容器 `/etc/nginx/conf.d/`）。

Cloudflare 隧道示例：`deploy/cloudflared/config.example.yml`

---



## 一、本地构建（不占服务器 CPU）



### Windows

```powershell
copy deploy\env\frontend-build.env.example deploy\env\frontend-build.env
# 填入 Cloudflare 隧道公网 https 域名
powershell -ExecutionPolicy Bypass -File deploy/scripts/build-release.ps1
```



### Linux / macOS

```bash
cp deploy/env/frontend-build.env.example deploy/env/frontend-build.env
bash deploy/scripts/build-release.sh
```

产物在 `deploy/release/`：

- `adminDist.tar.gz`、`sellerDist.tar.gz`、`customerDist.tar.gz`
- `backend.tar.gz`
- `deploy.tar.gz`（部署脚本、cron、nginx 模板）

---



## 二、上传到服务器

**示例（SSH 端口 2005）：**

```bash
# 全量
scp -P 2005 deploy/release/*.tar.gz root@121.196.192.200:/var/www/admin/

# 仅后端
scp -P 2005 deploy/release/backend.tar.gz root@121.196.192.200:/var/www/admin/

# 仅 deploy 脚本
scp -P 2005 deploy/release/deploy.tar.gz root@121.196.192.200:/var/www/admin/
```

也可上传整个 `deploy/` 目录（首次部署）：

```bash
scp -P 2005 -r deploy root@121.196.192.200:/var/www/admin/
```

> `build-release` 仅在**开发机**执行，不要在服务器上运行。

---



## 三、服务器首次初始化

```bash
# 1. 修改 nginx 三个 server_name 为隧道公网域名
vi /var/www/admin/deploy/nginx/08-ecommerce-admin.conf
# ...

# 2. 复制到 Nginx 配置挂载目录（容器内即 /etc/nginx/conf.d/）
cp /var/www/admin/deploy/nginx/0*-ecommerce-*.conf /opt/config/nginx/conf.d/

# 3. 后端 .env（CORS/CSRF 用 https 公网域名）
cp /var/www/admin/deploy/env/backend.env.example /var/www/admin/backend/.env
vi /var/www/admin/backend/.env

# 4. 部署应用
cd /var/www/admin && bash deploy/scripts/server-deploy-all.sh

# 5. 重载 Nginx 容器
docker exec <nginx容器名> nginx -t && docker exec <nginx容器名> nginx -s reload
```

---



## 四、后续更新



### 仅前端变更

```bash
# 1. 本地构建（Windows 见上文 build-release.ps1）
powershell -ExecutionPolicy Bypass -File deploy/scripts/build-release.ps1
# 2. 上传并解压
scp -P 2005 deploy/release/adminDist.tar.gz deploy/release/sellerDist.tar.gz deploy/release/customerDist.tar.gz root@121.196.192.200:/var/www/admin/
ssh -p 2005 root@121.196.192.200 "bash /var/www/admin/deploy/scripts/server-deploy-frontends.sh && docker exec nginx nginx -s reload"
```



### 含后端 / 数据库变更

```bash
scp -P 2005 deploy/release/backend.tar.gz deploy/release/deploy.tar.gz root@121.196.192.200:/var/www/admin/
ssh -p 2005 root@121.196.192.200
cd /var/www/admin && tar -xzf deploy.tar.gz
bash deploy/scripts/server-install-backend.sh /var/www/admin/backend.tar.gz
```

脚本会自动 `migrate` 与 `sync_menus`（同步侧栏菜单）；**已有库不会重复** `init_data`。补演示数据时手动：

```bash
cd /var/www/admin/backend && source venv/bin/activate
python manage.py migrate
python manage.py sync_menus
python manage.py init_data   # 仅首次或需要重置演示数据时
systemctl restart ecommerce-backend
```

**导航未更新时**（常见于只部署后端、未跑菜单同步）：

```bash
python manage.py sync_menus
systemctl restart ecommerce-backend
```

平台侧栏菜单来自数据库 RBAC，不是前端写死的；**商家端侧栏**在 `seller/src/config/menu.js`，需重新构建并部署 `sellerDist`。

### 一键全量（首次或大版本）

```bash
cd /var/www/admin && bash deploy/scripts/server-deploy-all.sh
docker exec <nginx容器名> nginx -t && docker exec <nginx容器名> nginx -s reload
```

---



## 五、常用命令

```bash
systemctl status ecommerce-backend
journalctl -u ecommerce-backend -f
docker exec <nginx容器名> nginx -t
```



### 定时任务（cron）


| 任务                      | 频率       | 说明             |
| ----------------------- | -------- | -------------- |
| `cancel_timeout_orders` | 每 5 分钟   | 待支付超时自动取消      |
| `auto_confirm_receipt`  | 每天 02:30 | 发货 15 天后自动确认收货 |
| `process_points_expiry` | 每天 02:00 | 积分过期提醒与自动扣减   |


安装：

```bash
sudo mkdir -p /var/log/ecommerce
sudo chmod +x /var/www/admin/deploy/scripts/run-scheduled-tasks.sh
sudo install -m 644 /var/www/admin/deploy/cron/ecommerce-backend.crontab /etc/cron.d/ecommerce-backend
```

详见 `deploy/cron/ecommerce-backend.crontab` 与 `deploy/scripts/run-scheduled-tasks.sh`。

---



## 六、Nginx 容器 + Cloudflare 隧道（无需 SSL）



### 为何不配 SSL

隧道对外已是 HTTPS，cloudflared 到源站 Nginx 走 HTTP 即可，**不要**在 Nginx 上配置 443 或证书。

### 环境变量协议


| 配置                         | 协议               |
| -------------------------- | ---------------- |
| `frontend-build.env`       | `https://`（公网域名） |
| `backend/.env` CORS / CSRF | `https://`（公网域名） |
| Nginx `listen`             | 仅 `80`           |




### Nginx 反代头

模板已设置 `proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;`，将隧道传入的 `https` 转给 Django。

### 端口


| 服务            | 端口                                              |
| ------------- | ----------------------------------------------- |
| 博客等           | 8000                                            |
| 其他            | 8001                                            |
| **电商 Daphne** | **8002**（默认，`backend/.env` 中 `BACKEND_PORT` 可改） |


改端口后：

```bash
bash /var/www/admin/deploy/scripts/sync-backend-port.sh
systemctl restart ecommerce-backend
docker exec <nginx> nginx -s reload
```

查看占用：`ss -tlnp | grep -E '800[0-9]'`

### 容器访问宿主机后端

若 Daphne 在**宿主机**、Nginx 在 **bridge 容器**内：

- **勿用** `host.docker.internal`（Linux 原生 Docker 不支持，会导致 `nginx -t` 失败）
- `BACKEND_UPSTREAM_HOST=172.17.0.1`（或 `docker network inspect bridge` 中的 Gateway）
- **`BACKEND_BIND=0.0.0.0`**（若仍为 `127.0.0.1`，容器访问 `172.17.0.1:8002` 会 **502**）
- 执行 `bash deploy/scripts/sync-backend-port.sh`（同步 `/api/`、`/ws/` 的 proxy_pass，**不要**改 `/media/` alias）

`/media/` 由 Nginx **alias 直读** `/var/www/admin/backend/media/`，容器需挂载该目录（建议整卷挂载 `/var/www/admin`）。

### 验证

```bash
curl -I https://admin.wangyixiang.xyz          # 经 Cloudflare
docker exec <nginx> nginx -T | grep server_name
```

---



## 七、演示账号（首次部署自动创建）

部署后端时若无 `admin` 用户，会自动执行 `python manage.py init_data`。  
**所有演示账号密码均为：**`admin123456`


| 端    | 登录地址                     | 账号                            | 说明             |
| ---- | ------------------------ | ----------------------------- | -------------- |
| 平台后台 | admin.wangyixiang.xyz    | `admin`                       | 超级管理员          |
| 平台后台 | 同上                       | `ops_staff`、`cs_staff` 等      | 见 init_data 输出 |
| 商户后台 | seller.wangyixiang.xyz   | `13900000001`                 | 张三的店           |
| 商户后台 | 同上                       | `13900000002`                 | 李四的店           |
| 用户商城 | customer.wangyixiang.xyz | `13800000000` ~ `13800000004` | 手机号 + 密码登录     |


已部署但无账号时，在服务器手动执行：

```bash
cd /var/www/admin/backend
source venv/bin/activate
python manage.py init_data
# 若仍提示「商户不存在」，单独补商户演示数据（需较新 backend 代码）：
python manage.py seed_seller_demo
```

商户登录账号为**手机号**或**店铺名**（如 `张三的店`），不是平台后台的 `ops_staff` 等用户名。

本地开发同样执行：`python adminAPI/manage.py init_data`

---



## 九、实时通知（红点 / WebSocket / 标题栏）

以下能力在 **admin / seller / customer 三端前端** 与 **Daphne 后端** 中实现，**仅部署后端不会生效**，必须重新构建并上传三份 `*Dist.tar.gz`。


| 能力      | 说明                                 |
| ------- | ---------------------------------- |
| 侧栏/铃铛红点 | WebSocket 推送 + 每 30 秒轮询兜底          |
| 标题栏未读数  | 常态 `(3) 站点名`                       |
| 新消息提示   | 收到推送时短暂显示 `【新消息】(3) 站点名`；后台标签页交替闪烁 |




### 部署检查清单

1. **后端必须用 Daphne（systemd** `ecommerce-backend`**）**，不要用 `runserver`。
2. **重新构建三端前端** 并部署：
  ```bash
   bash deploy/scripts/build-release.sh
   scp deploy/release/adminDist.tar.gz deploy/release/sellerDist.tar.gz deploy/release/customerDist.tar.gz root@server:/var/www/admin/
   bash /var/www/admin/deploy/scripts/server-deploy-frontends.sh
  ```
3. **Nginx 已配置** `/ws/` **反代**（见 `deploy/nginx/0*-ecommerce-*.conf`）。Nginx 在 Docker 内、Daphne 在宿主机时，将 `127.0.0.1:8002` 改为 `host.docker.internal:8002`（API 与 WS 同一地址）。
4. 更新 Nginx 配置后：`docker exec <nginx> nginx -t && docker exec <nginx> nginx -s reload`
5. **（可选）生产多 worker 时** 在 `backend/.env` 配置 `REDIS_URL=redis://127.0.0.1:6379/0`，否则 Channel Layer 使用进程内内存（单 Daphne 进程可正常工作）。



### 验证 WebSocket

浏览器登录后打开开发者工具 → Network → WS，应看到：

```
wss://admin.wangyixiang.xyz/ws/notify/?token=...
Status: 101 Switching Protocols
```

若 WS 失败，红点仍会通过 **30 秒轮询** 更新（稍慢）。若 API 也失败，检查 Nginx 反代与 `BACKEND_PORT`。

### 图片上传成功但 `/media/` 404

**现象**：`https://admin.wangyixiang.xyz/media/products/...` 返回 404，上传接口却 200。

**常见原因**：

1. **`DEBUG=False` 时 Django 未注册 `/media/` 路由**（已通过 `config/urls.py` 修复，需部署新 backend 并 `systemctl restart ecommerce-backend`）。
2. **Nginx 仍反代到 Daphne，但磁盘上无文件** — 在服务器检查：
   ```bash
   ls -la /var/www/admin/backend/media/products/2026/06/
   curl -I "http://127.0.0.1:8002/media/products/2026/06/文件名.png"
   ```
3. **Nginx 容器未挂载 media 目录** — 模板已改为 `alias /var/www/admin/backend/media/`，容器需能访问该路径（与 `adminDist` 同卷挂载 `/var/www/admin` 即可）。更新配置后：
   ```bash
   # .env 中 Linux 请用 172.17.0.1，不要用 host.docker.internal
   bash /var/www/admin/deploy/scripts/sync-backend-port.sh
   docker exec nginx nginx -t && docker exec nginx nginx -s reload
   # 确认容器内能看到文件
   docker exec nginx ls /var/www/admin/backend/media/products/2026/06/
   ```
4. **`nginx -t` 报 host.docker.internal 找不到** — 见上文，改 `BACKEND_UPSTREAM_HOST=172.17.0.1` 后重新 sync。

### API / 登录 502 Bad Gateway

**现象**：图片 `/media/` 已 200，但 `/api/` 返回 502。

**原因**：Nginx 在 Docker 内，`proxy_pass http://127.0.0.1:8002` 指向**容器自身**；且 Daphne 若只监听 `127.0.0.1:8002`，容器经 `172.17.0.1:8002` 也无法连上宿主机。

**修复**（在服务器执行）：

```bash
# 1. Daphne 监听所有网卡（供 Docker 网桥访问）
sed -i 's/^BACKEND_BIND=.*/BACKEND_BIND=0.0.0.0/' /var/www/admin/backend/.env
systemctl restart ecommerce-backend
ss -tlnp | grep 8002   # 应看到 0.0.0.0:8002

# 2. Nginx /api、/ws 指宿主机网关（勿用 127.0.0.1）
bash /var/www/admin/deploy/scripts/sync-backend-port.sh
# 若无新脚本，手动替换：
sed -i 's|proxy_pass http://127.0.0.1:8002/|proxy_pass http://172.17.0.1:8002/|g' \
  /opt/config/nginx/conf.d/0*-ecommerce-*.conf

# 3. 从 Nginx 容器内验证（应非 502）
docker exec nginx curl -sI -H 'Host: admin.wangyixiang.xyz' http://172.17.0.1:8002/api/auth/captcha/

docker exec nginx nginx -t && docker exec nginx nginx -s reload
```

### 后端变更后

```bash
cd /var/www/admin/backend && source venv/bin/activate
python manage.py migrate
systemctl restart ecommerce-backend
```

---



## 十、其他说明

- 三个前台 API 走同域 `/api`，构建时 `VITE_API_BASE_URL=/api` 即可。
- WebSocket 经隧道 + Nginx `/ws/` 反代，页面为 https 时浏览器自动使用 `wss://`。
- `server-install-backend.sh` 会保留已有 `.env`、`media/`、`db.sqlite3`；已有数据库不会重复 init_data。
- **本次及后续功能变更清单（需后端部署）**：标签系统 `tag_system`、平台商品打标 API、商家客户数按下单去重统计、仪表盘取消订单/金额格式化等——部署后请确认 `python manage.py migrate` 无报错。

