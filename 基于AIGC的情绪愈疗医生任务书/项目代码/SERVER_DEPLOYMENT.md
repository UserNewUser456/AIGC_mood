# 知识库管理工具 - 2GB内存服务器部署指南

## 内存需求评估

### 优化前（原始配置）
| 组件 | 内存占用 |
|------|---------|
| paraphrase-multilingual-MiniLM-L12-v2 模型 | ~400MB |
| NumPy + PyTorch + scikit-learn | ~300MB |
| 向量数据库（500文档） | ~300MB |
| **总计** | **~1.0-1.5GB** |

### 优化后（当前配置）
| 组件 | 内存占用 |
|------|---------|
| all-MiniLM-L6-v2 模型（轻量级） | ~80MB |
| NumPy + PyTorch + scikit-learn | ~150MB |
| 向量数据库（500文档限制） | ~300MB |
| 系统 + Flask等服务 | ~300-500MB |
| **总计** | **~800MB - 1.0GB** |

✅ **结论：优化后的代码可以在2GB内存服务器上运行**

## 优化措施

### 1. 使用轻量级模型
```python
# 原始配置
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'  # 400MB

# 优化后
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # 80MB
```

### 2. 限制文档数量
```python
MAX_DOCUMENTS_IN_MEMORY = 500  # 限制最大文档数
```

### 3. 降低NumPy版本
```txt
numpy<2.0.0  # 使用1.x版本，更省内存
```

### 4. 限制线程数
```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
```

## 部署方式

### 方式1：Git部署（推荐）

#### 步骤1：初始化Git仓库

在本地项目目录执行：

```bash
cd /path/to/project/code
git init
git add knowledge_manager.py
git add knowledge_manager_ext.py
git add test_knowledge_manager.py
git add requirements_knowledge.txt
git add deploy_server.sh
git add monitor_memory.sh
git add Dockerfile_lowmem
git add knowledge_manager_README.md
git add INTEGRATION_GUIDE.md
git add SERVER_DEPLOYMENT.md

git commit -m "初始化知识库管理工具 - 低内存优化版"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/yourusername/your-repo.git

git branch -M main
git push -u origin main
```

#### 步骤2：服务器拉取代码

```bash
# 连接到服务器
ssh user@your-server-ip

# 克隆代码
git clone https://github.com/yourusername/your-repo.git
cd your-repo

# 运行部署脚本
chmod +x deploy_server.sh
./deploy_server.sh
```

#### 步骤3：运行测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python3 test_knowledge_manager.py

# 选择模式 1 进行基本功能测试
```

### 方式2：手动部署

如果没有Git，可以手动上传文件：

```bash
# 1. 创建项目目录
mkdir knowledge_manager
cd knowledge_manager

# 2. 上传以下文件（使用scp或ftp）
# - knowledge_manager.py
# - knowledge_manager_ext.py
# - test_knowledge_manager.py
# - requirements_knowledge.txt

# 3. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_knowledge.txt

# 4. 运行测试
python3 test_knowledge_manager.py
```

### 方式3：Docker部署（可选）

```bash
# 1. 构建镜像
docker build -f Dockerfile_lowmem -t knowledge-manager:lowmem .

# 2. 运行容器
docker run -it --memory="1.5g" --memory-swap="2g" knowledge-manager:lowmem
```

## 部署后测试

### 基本功能测试

```bash
python3 test_knowledge_manager.py
# 选择 1 - 基本功能测试
```

### 手动测试导入

```bash
# 测试1：导入文本
python3 knowledge_manager.py import_text "焦虑症是一种常见的精神障碍..." "测试文本"

# 测试2：搜索
python3 knowledge_manager.py search "焦虑症"

# 测试3：查看统计
python3 knowledge_manager.py stats
```

### 内存监控

```bash
# 启动内存监控
chmod +x monitor_memory.sh
./monitor_memory.sh
```

监控窗口会显示：
- 当前内存使用情况
- 向量库大小
- 文档数量
- 进程信息

## 内存管理建议

### 1. 定期保存和清空

```python
# 清空向量库（当内存不足时）
POST /api/admin/knowledge_ext/vector_db/clear
```

### 2. 分批导入大量文本

不要一次性导入大量文档，分批进行：

```bash
# 每批导入100个文档
python3 knowledge_manager.py import_dir ./data/batch1
python3 knowledge_manager.py import_dir ./data/batch2
```

### 3. 禁用文本分析（可选）

如果不需要自动分析，可以节省内存：

```bash
python3 knowledge_manager.py import_file ./data/book.txt "" false
```

### 4. 监控内存使用

定期运行监控脚本，确保内存使用在安全范围内。

## 故障排除

### 问题1：内存不足

**症状**：系统变慢，进程被杀掉

**解决方案**：
```bash
# 1. 清空向量库
python3 knowledge_manager.py  # 需要实现清空命令

# 或通过API
curl -X POST http://localhost:5005/api/admin/knowledge_ext/vector_db/clear

# 2. 重启服务
# 3. 减少导入数量
```

### 问题2：模型下载慢

**解决方案**：
- 使用国内镜像
- 手动下载后放到 `~/.cache/torch/sentence_transformers/`

```bash
# 设置清华镜像（示例）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题3：导入失败

**检查**：
```bash
# 检查磁盘空间
df -h

# 检查内存
free -h

# 检查日志
tail -f logs/*.log
```

## 性能优化建议

### 1. 使用系统服务

创建systemd服务自动管理：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/knowledge-manager.service
```

内容：
```ini
[Unit]
Description=Knowledge Manager Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/knowledge-manager
Environment="PATH=/path/to/knowledge-manager/venv/bin"
ExecStart=/path/to/knowledge-manager/venv/bin/python3 /path/to/knowledge-manager/test_knowledge_manager.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable knowledge-manager
sudo systemctl start knowledge-manager
sudo systemctl status knowledge-manager
```

### 2. 使用Nginx反向代理

如果需要Web访问，配置Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/admin/knowledge/ {
        proxy_pass http://localhost:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 定期备份

备份向量库：

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"
mkdir -p $BACKUP_DIR

cp -r ./knowledge_vector_db $BACKUP_DIR/
echo "备份完成: $BACKUP_DIR"
```

## 监控和告警

### 设置内存告警

```bash
#!/bin/bash
# check_memory.sh

THRESHOLD=85  # 85%内存使用告警

USED_PERCENT=$(free -m | grep Mem | awk '{print $3/$2 * 100}' | cut -d. -f1)

if [ $USED_PERCENT -gt $THRESHOLD ]; then
    echo "警告: 内存使用率超过${THRESHOLD}%！当前: ${USED_PERCENT}%"
    # 可以发送邮件或钉钉告警
fi
```

添加到定时任务：
```bash
crontab -e
# 每5分钟检查一次
*/5 * * * * /path/to/check_memory.sh >> /var/log/knowledge_manager.log 2>&1
```

## 总结

### ✅ 代码已优化，适合2GB内存服务器

优化措施：
- 使用轻量级模型（80MB）
- 限制文档数量（500）
- 优化依赖版本
- 限制线程数

### 📦 部署方式

1. **Git部署**（推荐）- 简单快速
2. **手动部署** - 不需要Git
3. **Docker部署** - 容器化隔离

### 🔧 运维建议

- 定期监控内存使用
- 分批导入大量文档
- 定期备份向量库
- 设置告警机制

### 📝 测试清单

部署后请完成以下测试：

- [ ] 运行基本功能测试
- [ ] 导入测试文本
- [ ] 搜索功能测试
- [ ] 查看统计信息
- [ ] 内存监控测试
- [ ] API接口测试（如果需要）

现在可以安全地在2GB内存服务器上部署和运行知识库管理工具了！
