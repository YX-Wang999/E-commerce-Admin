# Windows 本地开发

日常使用：双击根目录 `start-dev.bat`，打开四个服务窗口；结束开发时双击 `stop-dev.bat`。
脚本仅适用于本地开发，不修改业务代码、`.env`，也不自动迁移或初始化数据库。

## 首次准备（或换电脑后）

安装 Python 和 Node.js。三个前端声明的 Node 版本为 `^22.14.0 || >=24.0.0`。
在项目根目录打开 PowerShell，执行：

```powershell
python -m venv adminAPI\.venv
.\adminAPI\.venv\Scripts\python.exe -m pip install -r .\adminAPI\requirements.txt
npm.cmd --prefix admin ci
npm.cmd --prefix customer ci
npm.cmd --prefix seller ci
```

已有可用 Python 环境时，无需重新创建。启动脚本依次优先使用：
`adminAPI\.venv`、`adminAPI\venv`、根目录 `.venv`、根目录 `venv`，最后是 PATH 中的 `python`（包括已激活的环境）。

检查 `adminAPI/.env`，缺失时可参考 `.env.example` 创建。当前项目配置使用 SQLite；
如果自行切换到 MySQL 或配置了 Redis，需要另外启动相应服务。
首次建立数据库或更新代码后有新迁移时，手动执行（使用实际选用的 Python）：

```powershell
cd adminAPI
.\.venv\Scripts\python.exe manage.py migrate
cd ..
```

脚本不会自动执行 `init_data`，避免每次启动改动已有开发数据。

## 日常启动

双击 `start-dev.bat`。路径中有中文或空格也可以，不必提前激活虚拟环境。

| 窗口名称 | 目录 | 地址 |
| --- | --- | --- |
| Ecommerce - Django :8000 | adminAPI | http://127.0.0.1:8000 |
| Ecommerce - admin :5173 | admin | http://localhost:5173 |
| Ecommerce - customer :5174 | customer | http://localhost:5174 |
| Ecommerce - seller :5175 | seller | http://localhost:5175 |

四个服务各自显示日志，启动失败的窗口保留错误输出。总入口显示“窗口已打开”不代表服务已经就绪，
请以各窗口日志为准；一个服务失败时，其他窗口继续运行，方便排查。

后端使用 `python -m daphne -b 127.0.0.1 -p 8000 config.asgi:application`，保留 WebSocket 支持。
三个前端的 `npm run dev` 当前均只执行 `vite`，脚本直接调用对应的 Vite 入口，避免 npm 改写窗口标题。
若将来修改 package.json 的 dev 脚本加入额外步骤，也应同步调整启动脚本。

启动器仅为子进程设置 `VITE_DEV_BACKEND=http://127.0.0.1:8000` 和 `VITE_API_BASE_URL=/api`，
使现有 Vite 代理将 API、媒体及 WebSocket 请求转发到本地后端，不受 `.env` 中部署端口影响。
不修改磁盘上的环境配置。

## 停止与重启

- **全部停止**：双击 `stop-dev.bat`。按本项目启动脚本路径识别四个 cmd 窗口，并用 `taskkill /T /F` 结束其进程树；会关闭窗口，未完成请求可能被中断。不会按进程名批量结束其他项目的 Python 或 Node。
- **单独停止**：在对应窗口按 `Ctrl+C`，如出现确认提示输入 `Y`，随后关闭该窗口。
- **重启**：先停止全部，再双击启动。Vue 修改通常会热更新；Daphne 不自动重载 Python 代码，后端修改后需要重启。

停止脚本只管理由本入口打开的服务；手动从其他终端启动的服务需在原终端停止。
请保留这四个窗口用于运行服务，不要在服务退出后用同一窗口执行无关任务，因为停止脚本会关闭这些窗口及其子进程。

## 常见问题

- **端口占用**：启动器检查 8000、5173、5174、5175，冲突时不启动任何服务；先停止旧服务或占用端口的程序。Vite 启用 `--strictPort`，不会悄悄切换端口。
- **缺少依赖**：按“首次准备”安装。启动器只检查基础模块和 Vite 入口，更具体的依赖或配置错误会显示在服务窗口。
- **接口报错**：查看 Django 窗口及数据库配置；后端根路径 `/` 没有页面不等于服务启动失败。
- **只检查环境**：在根目录运行 `cmd /c start-dev.bat --check`，不会启动服务或修改数据库。
- **停止失败**：在仍运行的服务窗口按 `Ctrl+C`。停止脚本依赖 Windows 的 PowerShell、CIM 和 taskkill。

新增文件仅有 `start-dev.bat`、`stop-dev.bat` 和本文档；没有额外进程管理依赖，也不创建 PID 文件。
