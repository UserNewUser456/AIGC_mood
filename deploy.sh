#!/bin/bash
# 服务器部署脚本

echo "==== 部署后端服务 ===="

# 1. 安装依赖
echo "安装依赖..."
pip install flask flask-cors pymysql pyjwt cryptography jieba

# 2. 创建后端目录
mkdir -p /var/www/aigc_backend

# 3. 下载代码（需要先在GitHub上获取）
# 如果没有git，需要先安装: apt-get install git
# git clone https://github.com/UserNewUser456/AIGC_mood.git /var/www/aigc_backend

echo "==== 部署完成 ===="
echo "请确保代码已下载到服务器"
echo ""
echo "启动服务:"
echo "  cd /var/www/aigc_backend"
echo "  python admin_server.py  # 端口5000"
echo "  python my_rag_knowledge_api.py  # 端口5001"
