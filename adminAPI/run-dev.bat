@echo off
REM Django ASGI server with WebSocket (Channels) support.
REM Do NOT use plain uvicorn without websockets — /ws/* will return 404.
cd /d "%~dp0"
daphne -b 0.0.0.0 -p 8000 config.asgi:application
