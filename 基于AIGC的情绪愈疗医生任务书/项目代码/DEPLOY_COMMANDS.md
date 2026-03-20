# 📋 服务器部署命令清单

## 🚀 完整部署命令（复制粘贴即可）

```bash
# ==================== 1. 连接到服务器 ====================
ssh username@your-server-ip

# ==================== 2. 克隆代码 ====================
git clone https://github.com/UserNewUser456/AIGC_mood.git
cd AIGC_mood/项目代码

# ==================== 3. 自动部署（5-10分钟）====================
chmod +x deploy_server.sh
./deploy_server.sh

# ==================== 4. 测试验证 ====================
chmod +x test_on_server.sh
./test_on_server.sh

# ==================== 5. 部署完成！====================
echo "✅ 部署完成！"
```

---

## 🎯 验证功能

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试导入文本
python3 knowledge_manager.py import_text "焦虑症是一种常见的精神障碍" "测试文档"

# 查看统计
python3 knowledge_manager.py stats

# 测试搜索
python3 knowledge_manager.py search "焦虑"

# 查看内存使用
free -h
```

---

## 📊 启动内存监控（可选）

```bash
chmod +x monitor_memory.sh
./monitor_memory.sh
# 按 Ctrl+C 退出
```

---

## 🔧 常用操作

```bash
# 导入文件
python3 knowledge_manager.py import_file /path/to/file.pdf

# 批量导入目录
python3 knowledge_manager.py import_dir /path/to/directory

# 搜索知识
python3 knowledge_manager.py search "关键词"

# 查看统计
python3 knowledge_manager.py stats

# 查看帮助
python3 knowledge_manager.py
```

---

## ⚠️ 故障排查

### pip安装慢
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements_knowledge.txt
```

### 模型下载慢
```bash
export HF_ENDPOINT=https://hf-mirror.com
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 内存不足
```bash
rm -rf knowledge_vector_db/vector_db.pkl
```

---

## 📚 查看文档

```bash
# 详细部署步骤
cat SERVER_STEP_BY_STEP.md

# 快速参考
cat SERVER_QUICK_REFERENCE.md

# 最终指南
cat FINAL_DEPLOYMENT_GUIDE.md
```

---

## ✅ 部署成功检查

- [ ] `./deploy_server.sh` 执行完成
- [ ] `./test_on_server.sh` 所有测试通过
- [ ] 内存使用率 < 80%
- [ ] 可以成功导入和搜索

---

**详细文档：** `FINAL_DEPLOYMENT_GUIDE.md`
