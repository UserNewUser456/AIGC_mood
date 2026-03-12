# Procfile - Railway部署启动命令
# 注意：Railway会自动使用railway.toml中的startCommand，此文件仅作备用

web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
