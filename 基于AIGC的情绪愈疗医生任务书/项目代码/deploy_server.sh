#!/bin/bash

# 知识库管理工具 - 服务器部署脚本
# 适合2GB内存的低配服务器

set -e

echo "=========================================="
echo "知识库管理工具 - 服务器部署"
echo "适合2GB内存服务器"
echo "=========================================="

# 1. 检查系统资源
echo ""
echo "[1] 检查系统资源..."
echo "可用内存:"
free -h
echo ""

# 检查内存是否足够
AVAILABLE_MEM=$(free -m | grep Mem | awk '{print $7}')
if [ $AVAILABLE_MEM -lt 1000 ]; then
    echo "警告: 可用内存不足1GB，部署可能失败"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. 更新系统（可选）
read -p "是否更新系统? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[2] 更新系统..."
    sudo apt-get update && sudo apt-get upgrade -y
fi

# 3. 安装Python和pip
echo ""
echo "[3] 检查Python..."
if ! command -v python3 &> /dev/null; then
    echo "安装Python 3..."
    sudo apt-get install -y python3 python3-pip python3-venv
else
    echo "Python已安装: $(python3 --version)"
fi

# 4. 创建虚拟环境（节省内存）
echo ""
echo "[4] 创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate

# 5. 升级pip
echo ""
echo "[5] 升级pip..."
pip install --upgrade pip

# 6. 安装依赖
echo ""
echo "[6] 安装Python依赖..."
pip install -r requirements_knowledge.txt

# 7. 检查磁盘空间
echo ""
echo "[7] 检查磁盘空间..."
df -h .

# 8. 创建必要的目录
echo ""
echo "[8] 创建必要的目录..."
mkdir -p knowledge_vector_db
mkdir -p knowledge_uploads
mkdir -p logs

# 9. 设置环境变量（低内存优化）
echo ""
echo "[9] 配置低内存优化..."
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# 保存到bashrc
if ! grep -q "OMP_NUM_THREADS" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# 低内存优化" >> ~/.bashrc
    echo "export OMP_NUM_THREADS=1" >> ~/.bashrc
    echo "export MKL_NUM_THREADS=1" >> ~/.bashrc
    echo "export OPENBLAS_NUM_THREADS=1" >> ~/.bashrc
    echo "export NUMEXPR_NUM_THREADS=1" >> ~/.bashrc
    echo "环境变量已保存到 ~/.bashrc"
fi

# 10. 下载模型（首次运行）
echo ""
echo "[10] 测试模型加载..."
python3 -c "from sentence_transformers import SentenceTransformer; print('正在下载模型...'); model = SentenceTransformer('all-MiniLM-L6-v2'); print('模型下载成功!')"

# 11. 测试功能
echo ""
echo "[11] 运行功能测试..."
python3 test_knowledge_manager.py <<EOF
1
EOF

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "使用说明："
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 运行测试: python3 test_knowledge_manager.py"
echo "3. 查看帮助: python3 knowledge_manager.py"
echo ""
echo "注意事项："
echo "- 已限制最大文档数为500，避免内存溢出"
echo "- 使用轻量级模型（约80MB）"
echo "- 建议定期保存和清空向量库"
echo "- 导入大量文本时请分批处理"
echo ""
