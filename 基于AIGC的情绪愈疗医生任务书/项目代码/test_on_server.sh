#!/bin/bash

# 服务器测试脚本
# 用于在2GB内存服务器上测试知识库管理工具

echo "=========================================="
echo "知识库管理工具 - 服务器测试"
echo "=========================================="

# 1. 检查Python版本
echo ""
echo "[1] 检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: Python3未安装"
    exit 1
fi

# 2. 检查虚拟环境
echo ""
echo "[2] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，请先运行 ./deploy_server.sh"
    exit 1
fi

source venv/bin/activate

# 3. 检查依赖
echo ""
echo "[3] 检查依赖..."
python3 -c "import sentence_transformers; import numpy; import sklearn; print('✓ 依赖已安装')"

if [ $? -ne 0 ]; then
    echo "错误: 依赖未安装，请运行: pip install -r requirements_knowledge.txt"
    exit 1
fi

# 4. 测试模型加载
echo ""
echo "[4] 测试模型加载..."
python3 -c "
from knowledge_manager import VectorStore
import time

print('正在加载模型...')
start = time.time()
vs = VectorStore()
end = time.time()
print(f'✓ 模型加载成功，耗时: {end-start:.2f}秒')
"

if [ $? -ne 0 ]; then
    echo "错误: 模型加载失败"
    exit 1
fi

# 5. 测试文本导入
echo ""
echo "[5] 测试文本导入..."
python3 -c "
from knowledge_manager import KnowledgeManager

manager = KnowledgeManager()

# 测试文本
test_text = '''
焦虑症是一种常见的精神障碍，表现为过度的担忧和紧张。
常见症状包括心悸、失眠、注意力不集中等。
治疗方法包括认知行为疗法、药物治疗和放松训练。
'''

result = manager.import_text(
    text=test_text,
    title='测试文本',
    source='测试脚本',
    analyze=False  # 跳过分析以节省API调用
)

if result['success']:
    print(f'✓ 文本导入成功: {result[\"message\"]}')
else:
    print(f'✗ 文本导入失败: {result.get(\"error\", \"Unknown\")}')
    exit(1)

# 保存向量库
manager.vector_store.save()
print('✓ 向量库已保存')
"

if [ $? -ne 0 ]; then
    echo "错误: 文本导入测试失败"
    exit 1
fi

# 6. 测试搜索
echo ""
echo "[6] 测试搜索功能..."
python3 -c "
from knowledge_manager import KnowledgeManager

manager = KnowledgeManager()
manager.load_vector_db()

queries = ['焦虑症', '治疗方法', '心悸失眠']

for query in queries:
    result = manager.search_knowledge(query, top_k=1)
    if result['success'] and result['data']['results']:
        item = result['data']['results'][0]
        print(f'✓ 搜索 \"{query}\" - 相似度: {item[\"score\"]:.3f}')
    else:
        print(f'✗ 搜索 \"{query}\" 失败')
        exit(1)
"

if [ $? -ne 0 ]; then
    echo "错误: 搜索测试失败"
    exit 1
fi

# 7. 测试统计
echo ""
echo "[7] 测试统计功能..."
python3 -c "
from knowledge_manager import KnowledgeManager

manager = KnowledgeManager()
manager.load_vector_db()

result = manager.get_stats()
if result['success']:
    data = result['data']
    print(f'✓ 统计信息:')
    print(f'  - 文档数: {data[\"total_documents\"]}')
    print(f'  - 导入次数: {data[\"total_imports\"]}')
else:
    print(f'✗ 获取统计失败: {result.get(\"error\", \"Unknown\")}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "错误: 统计测试失败"
    exit 1
fi

# 8. 检查内存使用
echo ""
echo "[8] 检查内存使用..."
ps aux | grep -E "python.*knowledge_manager" | grep -v grep | awk '{
    if ($4 != "") {
        print("  Python进程 - CPU:", $3"%, 内存:", $4"%")
    }
}'

MEMORY_INFO=$(free -m | grep Mem)
AVAILABLE_MEM=$(echo $MEMORY_INFO | awk '{print $7}')
TOTAL_MEM=$(echo $MEMORY_INFO | awk '{print $2}')
USED_PERCENT=$((100 - AVAILABLE_MEM * 100 / TOTAL_MEM))

echo "  系统内存 - 可用: ${AVAILABLE_MEM}MB / 总计: ${TOTAL_MEM}MB"
echo "  使用率: ${USED_PERCENT}%"

if [ $USED_PERCENT -gt 80 ]; then
    echo "  ⚠️  警告: 内存使用率超过80%"
else
    echo "  ✓ 内存使用正常"
fi

# 9. 检查磁盘空间
echo ""
echo "[9] 检查磁盘空间..."
df -h . | grep -v Filesystem | awk '{
    print("  磁盘使用:", $3 "/", $2, "(" $5 ")")
}'

# 10. 总结
echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "所有测试通过 ✓"
echo ""
echo "下一步："
echo "1. 启动内存监控: ./monitor_memory.sh"
echo "2. 导入实际数据: python3 knowledge_manager.py import_file <文件路径>"
echo "3. 集成到admin_server.py: 参考 INTEGRATION_GUIDE.md"
echo ""
