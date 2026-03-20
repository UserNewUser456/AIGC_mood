# 在服务器上部署知识库管理工具 - 详细操作指南

## 📋 前提条件确认

### 服务器信息
- **操作系统**: Linux (Ubuntu/CentOS/Debian)
- **内存**: 2GB
- **Python版本**: 3.8+
- **网络**: 需要访问GitHub和pip源

### 本地准备
- ✅ 代码已推送到GitHub
- ✅ 准备好服务器的IP地址和登录凭证

---

## 🚀 部署步骤

### 第一步：连接到服务器

```bash
# SSH连接到服务器
ssh username@your-server-ip

# 例如:
# ssh root@192.168.1.100
# 或
# ssh ubuntu@123.45.67.89
```

**如果提示输入密码，请输入您的服务器登录密码。**

---

### 第二步：克隆代码

```bash
# 进入服务器的工作目录（可选）
cd ~

# 克隆Git仓库
git clone https://github.com/UserNewUser456/AIGC_mood.git

# 进入项目目录
cd AIGC_mood/项目代码

# 查看文件列表
ls -lh
```

**预期输出应该包含以下文件：**
```
knowledge_manager.py
knowledge_manager_ext.py
test_knowledge_manager.py
requirements_knowledge.txt
deploy_server.sh
test_on_server.sh
monitor_memory.sh
QUICKSTART.md
DEPLOYMENT_SUMMARY.md
...
```

---

### 第三步：运行部署脚本

```bash
# 给部署脚本添加执行权限
chmod +x deploy_server.sh

# 运行部署脚本
./deploy_server.sh
```

**部署脚本会自动执行以下操作：**
1. ✅ 检查系统内存（确保至少1GB可用）
2. ✅ 检查Python3是否安装
3. ✅ 创建Python虚拟环境（节省内存）
4. ✅ 升级pip
5. ✅ 安装所有Python依赖
6. ✅ 创建必要的目录（knowledge_vector_db, knowledge_uploads, logs）
7. ✅ 配置低内存优化环境变量
8. ✅ 下载模型（all-MiniLM-L6-v2，约80MB）
9. ✅ 运行基本功能测试

**预计耗时：5-10分钟（取决于网络速度）**

---

### 第四步：运行测试脚本

```bash
# 给测试脚本添加执行权限
chmod +x test_on_server.sh

# 运行测试脚本
./test_on_server.sh
```

**测试脚本会验证：**
1. ✅ Python版本
2. ✅ 虚拟环境
3. ✅ Python依赖
4. ✅ 模型加载
5. ✅ 文本导入功能
6. ✅ 搜索功能
7. ✅ 统计功能
8. ✅ 内存使用情况
9. ✅ 磁盘空间

**预期输出（示例）：**
```
==========================================
知识库管理工具 - 服务器测试
==========================================

[1] 检查Python版本...
Python 3.10.12

[2] 检查虚拟环境...

[3] 检查依赖...
✓ 依赖已安装

[4] 测试模型加载...
正在加载模型...
✓ 模型加载成功，耗时: 2.35秒

[5] 测试文本导入...
✓ 文本导入成功: 文档已添加到向量库
✓ 向量库已保存

[6] 测试搜索功能...
✓ 搜索 "焦虑症" - 相似度: 0.892
✓ 搜索 "治疗方法" - 相似度: 0.876
✓ 搜索 "心悸失眠" - 相似度: 0.823

[7] 测试统计功能...
✓ 统计信息:
  - 文档数: 1
  - 导入次数: 1

[8] 检查内存使用...
  系统内存 - 可用: 1150MB / 总计: 2048MB
  使用率: 43%
  ✓ 内存使用正常

[9] 检查磁盘空间...
  磁盘使用: 2.5G / 20G (13%)

==========================================
测试完成！
==========================================

所有测试通过 ✓
```

---

### 第五步：测试基本功能

```bash
# 激活虚拟环境
source venv/bin/activate

# 1. 测试导入文本
python3 knowledge_manager.py import_text "焦虑症是一种常见的精神障碍，表现为过度的担忧和紧张。" "焦虑症介绍"

# 2. 查看统计信息
python3 knowledge_manager.py stats

# 3. 测试搜索
python3 knowledge_manager.py search "焦虑症状"

# 4. 测试导入文件（如果有测试文件）
# python3 knowledge_manager.py import_file ./test.txt
```

---

## 📊 监控和维护

### 启动内存监控

```bash
# 给监控脚本添加执行权限
chmod +x monitor_memory.sh

# 运行内存监控
./monitor_memory.sh
```

**监控脚本会实时显示：**
- Python进程的CPU和内存使用
- 系统总体内存使用情况
- 向量库文件大小

**按 `Ctrl+C` 退出监控。**

---

## 🔧 常见问题排查

### 问题1：Git clone失败

**错误信息：**
```
fatal: unable to access 'https://github.com/...': Failed to connect to github.com
```

**解决方案：**
```bash
# 检查网络连接
ping github.com

# 如果网络不通，可能需要配置代理
export https_proxy=http://your-proxy:port
export http_proxy=http://your-proxy:port

# 或者使用其他镜像站点
```

---

### 问题2：pip安装依赖失败

**错误信息：**
```
ERROR: Could not find a version that satisfies the requirement...
```

**解决方案：**

**方法1：使用国内镜像**
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements_knowledge.txt
```

**方法2：使用豆瓣镜像**
```bash
pip config set global.index-url https://pypi.doubanio.com/simple
pip install -r requirements_knowledge.txt
```

---

### 问题3：模型下载太慢或失败

**错误信息：**
```
OSError: Can't load tokenizer for 'all-MiniLM-L6-v2'
```

**解决方案：**

**方法1：手动下载模型**
```bash
# 激活环境
source venv/bin/activate

# 使用国内HuggingFace镜像
export HF_ENDPOINT=https://hf-mirror.com

# 测试下载
python3 -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2'); print('模型下载成功')"
```

**方法2：预下载模型文件**
```bash
# 在本地下载模型，然后上传到服务器
# 本地执行:
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 上传缓存目录到服务器
# Windows: C:\Users\<username>\.cache\huggingface\hub
# Linux: ~/.cache/huggingface/hub

# 服务器上创建目录
mkdir -p ~/.cache/huggingface/hub

# 将缓存文件复制到服务器的 ~/.cache/huggingface/hub/
```

---

### 问题4：内存不足

**错误信息：**
```
MemoryError: Unable to allocate array...
```

**解决方案：**

```bash
# 1. 清空向量库
rm -rf knowledge_vector_db/vector_db.pkl

# 2. 重启服务或重新加载
source venv/bin/activate

# 3. 检查内存使用
free -h

# 4. 分批导入，不要一次性导入太多文档
python3 knowledge_manager.py import_dir ./batch1
# 等待一段时间
python3 knowledge_manager.py import_dir ./batch2
```

---

### 问题5：Python版本太低

**错误信息：**
```
SyntaxError: invalid syntax
```

**解决方案：**

```bash
# 检查Python版本
python3 --version

# 如果低于3.8，需要升级Python
# Ubuntu 20.04+
sudo apt-get update
sudo apt-get install -y python3.8 python3-pip python3.8-venv

# CentOS/RHEL
sudo yum install -y python3 python3-pip

# 或者使用pyenv安装新版本Python
curl https://pyenv.run | bash
pyenv install 3.10.12
pyenv global 3.10.12
```

---

## 📝 集成到管理员后台

如果要将知识库管理工具集成到现有的管理员后台，请参考 `INTEGRATION_GUIDE.md`。

### 快速集成步骤

```bash
# 1. 复制扩展文件到admin_server目录
cp knowledge_manager_ext.py /path/to/admin_server/

# 2. 在admin_server.py中导入蓝图
from knowledge_manager_ext import knowledge_ext_bp

# 3. 注册蓝图
app.register_blueprint(knowledge_ext_bp)

# 4. 重启admin_server
python3 admin_server.py
```

---

## 🔄 自动化部署脚本

如果需要多次部署，可以创建一个一键部署脚本：

```bash
# 创建一键部署脚本
cat > deploy_all.sh << 'EOF'
#!/bin/bash

set -e

echo "开始一键部署..."

# 步骤1: 克隆或更新代码
if [ -d "AIGC_mood" ]; then
    cd AIGC_mood/项目代码
    git pull
else
    git clone https://github.com/UserNewUser456/AIGC_mood.git
    cd AIGC_mood/项目代码
fi

# 步骤2: 运行部署脚本
chmod +x deploy_server.sh
./deploy_server.sh

# 步骤3: 运行测试脚本
chmod +x test_on_server.sh
./test_on_server.sh

echo "部署完成！"
EOF

chmod +x deploy_all.sh
./deploy_all.sh
```

---

## 📞 获取帮助

如果遇到其他问题：

1. **查看详细日志**
```bash
# 查看部署日志
./deploy_server.sh 2>&1 | tee deploy.log

# 查看测试日志
./test_on_server.sh 2>&1 | tee test.log
```

2. **检查系统状态**
```bash
# 检查内存
free -h

# 检查磁盘
df -h

# 检查进程
ps aux | grep python
```

3. **查看文档**
- `QUICKSTART.md` - 快速开始指南
- `SERVER_DEPLOYMENT.md` - 详细部署指南
- `knowledge_manager_README.md` - 使用文档
- `INTEGRATION_GUIDE.md` - 集成指南

---

## ✅ 验证部署成功

部署成功的标志：

1. ✅ `./deploy_server.sh` 执行完成，无错误
2. ✅ `./test_on_server.sh` 所有测试通过
3. ✅ 可以成功导入文本
4. ✅ 可以成功搜索知识
5. ✅ 内存使用率在80%以下
6. ✅ 模型加载正常（约80MB）

---

## 🎉 下一步

部署成功后，您可以：

1. **导入实际的心理学知识库**
```bash
python3 knowledge_manager.py import_file /path/to/psychology_book.pdf
```

2. **批量导入目录**
```bash
python3 knowledge_manager.py import_dir /path/to/books
```

3. **集成到管理员后台**
参考 `INTEGRATION_GUIDE.md`

4. **设置定期备份**
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp -r knowledge_vector_db backups/$DATE
echo "备份完成: backups/$DATE"
EOF

chmod +x backup.sh
mkdir -p backups

# 设置定时任务（每天凌晨2点备份）
crontab -e
# 添加以下行:
# 0 2 * * * /path/to/backup.sh >> /var/log/km_backup.log 2>&1
```

5. **设置开机自启**
```bash
# 创建systemd服务文件
sudo cat > /etc/systemd/system/knowledge-manager.service << 'EOF'
[Unit]
Description=Knowledge Manager Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/AIGC_mood/项目代码
Environment="PATH=/path/to/AIGC_mood/项目代码/venv/bin"
ExecStart=/path/to/AIGC_mood/项目代码/venv/bin/python3 /path/to/AIGC_mood/项目代码/knowledge_manager_ext.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable knowledge-manager
sudo systemctl start knowledge-manager
```

---

**祝您部署顺利！如有问题，请参考上述排查步骤。** 🚀
