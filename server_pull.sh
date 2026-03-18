#!/bin/bash
# 服务器部署脚本 - 拉取核心代码

echo "开始从Git拉取代码..."

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

# 保留测试脚本的.gitkeep文件（如果需要）
# rm -f test_*.py check_services.py quick_*.py

echo "代码更新完成！"
