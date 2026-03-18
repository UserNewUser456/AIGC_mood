@echo off
REM 服务器启动批处理脚本
REM 使用方法: 双击运行此脚本，或在命令行中运行

echo ========================================
echo AI情感陪伴平台 - 服务器启动脚本
echo ========================================
echo.
echo 请在服务器上执行以下命令:
echo.
echo 步骤1: 启动Neo4j
echo   neo4j start
echo.
echo 步骤2: 启动管理员后台 (端口5005)
echo   cd /root/AIGC_mood
echo   python3 admin_server.py
echo.
echo 步骤3: 启动RAG知识图谱服务 (端口5001)
echo   cd /root/AIGC_mood
echo   python3 my_rag_knowledge_api.py
echo.
echo ========================================
echo 启动完成后，在本地运行以下命令测试:
echo   python test_rag_api.py
echo ========================================
pause
