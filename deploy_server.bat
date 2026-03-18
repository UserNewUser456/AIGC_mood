@echo off
chcp 65001 >nul
echo ========================================
echo Git Pull 并部署到服务器
echo ========================================
echo.

echo 正在连接服务器并执行命令...

ssh -o ConnectTimeout=30 root@49.235.105.137 "cd /root/AIGC_mood && git pull origin master"

echo.
echo 安装依赖...
ssh root@49.235.105.137 "pip install PyPDF2 python-docx -q"

echo.
echo 重启Neo4j...
ssh root@49.235.105.137 "neo4j start"

echo.
echo 重启管理员后台 (5005)...
ssh root@49.235.105.137 "pkill -f admin_server; cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &"

echo.
echo 重启RAG服务 (5001)...
ssh root@49.235.105.137 "pkill -f my_rag_knowledge_api; cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &"

echo.
echo 重启文档知识API (5002)...
ssh root@49.235.105.137 "pkill -f document_knowledge_api; cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &"

echo.
echo 检查服务状态...
ssh root@49.235.105.137 "netstat -tlnp | grep -E ':(5001|5002|5005)'"

echo.
echo ========================================
echo 部署完成！
echo 服务地址:
echo   管理员后台: http://49.235.105.137:5005
echo   RAG知识图谱: http://49.235.105.137:5001
echo   文档知识API: http://49.235.105.137:5002
echo ========================================
pause
