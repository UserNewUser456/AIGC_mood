#!/bin/bash
# 服务器部署脚本 - 只保留核心代码

echo "开始从Git拉取核心代码..."

cd /root/AIGC_mood

# 检查是否是git仓库
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git remote add origin https://github.com/UserNewUser456/AIGC_mood.git
fi

# 拉取最新代码
echo "正在拉取代码..."
git pull origin master

# 删除测试和临时脚本（保留核心功能）
echo "清理测试文件..."
rm -f test_*.py check_services.py quick_*.py restart_*.py
rm -f deploy_*.py git_deploy.py install_and_fix.py
rm -f simple_test.py ssh_*.py t1.py
rm -f start_all_services.sh start_server.exp start_rag.bat
rm -f start_services.bat fix_neo4j.py

echo "核心代码部署完成！"
echo ""
echo "请重启服务："
echo "  - 管理员API (5005): python admin_server.py"
echo "  - RAG API (5001): python my_rag_knowledge_api.py"
echo "  - 文档API (5002): python document_knowledge_api.py"
