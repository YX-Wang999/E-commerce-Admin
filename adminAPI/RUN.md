# 本地启动后端

## 推荐（支持 WebSocket 通知 / 聊天）

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Windows 可直接双击 `run-dev.bat`。

## 不要用裸 uvicorn（除非已装 websockets）

```bash
# 错误示例 — WebSocket 会 404：
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

未安装 `websockets` 时，uvicorn 无法完成 WebSocket 升级，`/ws/notify/` 会被当成普通 HTTP GET，Django 返回 **404**。

若必须使用 uvicorn：

```bash
pip install "uvicorn[standard]"
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

生产环境同样使用 **daphne**（见 `deploy/systemd/ecommerce-backend.service`）。
