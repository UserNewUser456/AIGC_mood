# 快速开始 - 在2GB内存服务器上部署

## 前提条件

- ✅ 代码已推送到GitHub: https://github.com/UserNewUser456/AIGC_mood.git
- ✅ 服务器内存: 2GB
- ✅ 操作系统: Linux (Ubuntu/CentOS等)
- ✅ Python 3.8+

## 快速部署（3步）

### 步骤1：克隆代码

```bash
# SSH连接到服务器
ssh user@your-server-ip

# 克隆仓库
git clone https://github.com/UserNewUser456/AIGC_mood.git
cd AIGC_mood/项目代码
```

### 步骤2：自动部署

```bash
# 运行部署脚本
chmod +x deploy_server.sh
./deploy_server.sh
```

部署脚本会自动：
- ✅ 检查系统资源
- ✅ 安装Python和依赖
- ✅ 创建虚拟环境
- ✅ 下载轻量级模型（80MB）
- ✅ 运行基本测试

### 步骤3：验证测试

```bash
# 运行测试脚本
chmod +x test_on_server.sh
./test_on_server.sh
```

测试脚本会验证：
- ✅ Python环境
- ✅ 依赖安装
- ✅ 模型加载
- ✅ 文本导入
- ✅ 搜索功能
- ✅ 统计功能
- ✅ 内存使用

## 使用方法

### 1. 激活环境

```bash
cd /path/to/AIGC_mood/项目代码
source venv/bin/activate
```

### 2. 导入文本

```bash
# 导入单个文本
python3 knowledge_manager.py import_text "文本内容..." "标题"

# 导入文件
python3 knowledge_manager.py import_file ./data/book.pdf

# 批量导入目录
python3 knowledge_manager.py import_dir ./data/books
```

### 3. 搜索知识

```bash
python3 knowledge_manager.py search "焦虑症状"
```

### 4. 查看统计

```bash
python3 knowledge_manager.py stats
```

### 5. 内存监控

```bash
# 实时监控内存使用
chmod +x monitor_memory.sh
./monitor_memory.sh

# 按Ctrl+C退出
```

## 内存管理

### 清空向量库（当内存不足时）

```bash
# 方法1: 删除向量库文件
rm -rf knowledge_vector_db/vector_db.pkl

# 方法2: 通过API清空（如果已集成到admin_server）
curl -X POST http://localhost:5005/api/admin/knowledge_ext/vector_db/clear
```

### 限制导入数量

```bash
# 分批导入，每批100个文档
python3 knowledge_manager.py import_dir ./data/batch1
# 等待一段时间
python3 knowledge_manager.py import_dir ./data/batch2
```

### 跳过文本分析（节省API调用和内存）

```bash
# 使用analyze=false参数
python3 knowledge_manager.py import_file ./data/book.txt "" false
```

## 常见问题

### Q: 模型下载太慢怎么办？

A: 使用国内镜像：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements_knowledge.txt
```

### Q: 内存不足怎么办？

A: 执行以下操作：

1. 清空向量库
2. 减少导入数量
3. 重启服务
4. 检查是否有其他进程占用内存

### Q: 如何查看详细日志？

A: 查看Python输出或创建日志文件：

```bash
python3 knowledge_manager.py stats 2>&1 | tee logs/manager.log
```

### Q: 如何集成到现有的Flask应用？

A: 参考 `INTEGRATION_GUIDE.md` 文档。

### Q: 如何设置开机自启？

A: 使用systemd：

```bash
sudo cp /path/to/knowledge-manager.service /etc/systemd/system/
sudo systemctl enable knowledge-manager
sudo systemctl start knowledge-manager
```

## 性能参考

### 内存使用（2GB服务器）

| 组件 | 内存占用 |
|------|---------|
| 模型（all-MiniLM-L6-v2） | ~80MB |
| Python运行时 | ~150MB |
| 向量库（500文档） | ~300MB |
| 系统其他 | ~300-500MB |
| **总计** | **~830-1030MB** |

### 导入速度

| 文档数量 | 大小 | 耗时 |
|---------|------|------|
| 1个（500字） | ~500B | ~1秒 |
| 100个 | ~50KB | ~30秒 |
| 500个 | ~250KB | ~2-3分钟 |

### 搜索速度

| 查询 | 耗时 |
|------|------|
| 单次搜索 | ~0.1-0.3秒 |
| 批量搜索（10个） | ~1-2秒 |

## 安全建议

1. **定期备份向量库**

```bash
#!/bin/bash
# backup_vector_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
cp -r knowledge_vector_db backups/$DATE
echo "备份完成: backups/$DATE"
```

2. **监控内存使用**

设置定时任务，每5分钟检查一次：

```bash
crontab -e
*/5 * * * * /path/to/monitor_memory.sh >> /var/log/km_monitor.log 2>&1
```

3. **限制API访问**

在Nginx或应用层添加认证：

```python
# 在knowledge_manager_ext.py中
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if not verify_token(token):
            return jsonify({'success': False, 'error': '未授权'}), 401
        return f(*args, **kwargs)
    return decorated

@knowledge_ext_bp.route('/search', methods=['GET'])
@require_auth
def search_knowledge():
    # ...
```

## 下一步

部署完成后，您可以：

1. ✅ 导入实际的心理学知识库
2. ✅ 集成到管理员后台（参考 `INTEGRATION_GUIDE.md`）
3. ✅ 配置前端界面
4. ✅ 设置定期备份
5. ✅ 监控系统性能

## 技术支持

- 📖 详细文档: `knowledge_manager_README.md`
- 🔧 集成指南: `INTEGRATION_GUIDE.md`
- 🚀 部署指南: `SERVER_DEPLOYMENT.md`
- 📝 原始文档: `RAG_基于知识图谱检索增强生成 - 副本.md`

## 总结

✅ **代码已推送到GitHub**
✅ **已优化适合2GB内存服务器**
✅ **包含完整的部署脚本和测试工具**
✅ **提供详细的使用文档**

**现在可以在服务器上安全运行了！**
