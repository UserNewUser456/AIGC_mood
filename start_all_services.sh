#!/bin/bash
# 服务器一键启动脚本

echo "=== 启动Neo4j ==="
neo4j start
sleep 5
neo4j status

echo ""
echo "=== 检查Neo4j连接 ==="
cypher-shell -u neo4j -p root1234 "RETURN 1" || echo "Neo4j认证可能有问题"

echo ""
echo "=== 启动管理员后台服务 (端口5005) ==="
cd /root/AIGC_mood
nohup python3 admin_server.py > /tmp/admin_server.log 2>&1 &
sleep 2
echo "管理员服务已启动"

echo ""
echo "=== 启动RAG知识图谱服务 (端口5001) ==="
nohup python3 my_rag_knowledge_api.py > /tmp/rag_api.log 2>&1 &
sleep 3
echo "RAG服务已启动"

echo ""
echo "=== 检查服务状态 ==="
netstat -tlnp | grep -E ':(5001|5005)'

echo ""
echo "=== 启动完成 ==="
echo "管理员后台: http://你的IP:5005"
echo "RAG API: http://你的IP:5001"
