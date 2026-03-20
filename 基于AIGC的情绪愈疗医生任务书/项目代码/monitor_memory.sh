#!/bin/bash

# 内存监控脚本 - 用于2GB内存服务器
# 实时监控内存使用情况

while true; do
    clear

    echo "=========================================="
    echo "知识库管理工具 - 内存监控"
    echo "=========================================="
    echo ""

    # 显示当前时间
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 显示内存使用情况
    echo "--- 内存使用情况 ---"
    free -h

    # 计算可用内存百分比
    TOTAL_MEM=$(free -m | grep Mem | awk '{print $2}')
    AVAILABLE_MEM=$(free -m | grep Mem | awk '{print $7}')
    USED_PERCENT=$((100 - AVAILABLE_MEM * 100 / TOTAL_MEM))

    echo ""
    echo "可用内存: ${AVAILABLE_MEM}MB / ${TOTAL_MEM}MB"
    echo "使用率: ${USED_PERCENT}%"

    # 警告
    if [ $USED_PERCENT -gt 85 ]; then
        echo ""
        echo "⚠️  警告: 内存使用率过高！建议重启服务或清空向量库"
    elif [ $USED_PERCENT -gt 70 ]; then
        echo ""
        echo "⚡ 注意: 内存使用率较高"
    fi

    echo ""
    echo "--- 向量库大小 ---"
    if [ -d "./knowledge_vector_db" ]; then
        du -sh ./knowledge_vector_db
    else
        echo "向量库目录不存在"
    fi

    echo ""
    echo "--- 文档数量 ---"
    if [ -f "./knowledge_vector_db/vector_db.pkl" ]; then
        python3 -c "
import pickle
import os
if os.path.exists('./knowledge_vector_db/vector_db.pkl'):
    with open('./knowledge_vector_db/vector_db.pkl', 'rb') as f:
        data = pickle.load(f)
        print(f'文档数: {len(data.get(\"documents\", []))}')
        print(f'向量数: {len(data.get(\"embeddings\", []))}'
"
    else
        echo "向量数据库文件不存在"
    fi

    echo ""
    echo "--- 进程信息 ---"
    ps aux | grep python | grep -v grep | awk '{print "PID:", $2, "CPU:", $3"%", "MEM:", $4"%", "CMD:", $11}'

    echo ""
    echo "按 Ctrl+C 退出监控"
    echo ""

    sleep 5
done
