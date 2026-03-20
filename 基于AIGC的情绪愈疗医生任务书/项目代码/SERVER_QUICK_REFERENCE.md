# 🚀 服务器快速部署 - 快速参考卡

## 📝 完整命令清单（复制粘贴即可）

### 1️⃣ 连接服务器
```bash
ssh username@your-server-ip
```

### 2️⃣ 克隆代码
```bash
git clone https://github.com/UserNewUser456/AIGC_mood.git
cd AIGC_mood/项目代码
```

### 3️⃣ 自动部署
```bash
chmod +x deploy_server.sh
./deploy_server.sh
```
**⏱️ 预计耗时：5-10分钟**

### 4️⃣ 测试验证
```bash
chmod +x test_on_server.sh
./test_on_server.sh
```

### 5️⃣ 启动内存监控
```bash
chmod +x monitor_memory.sh
./monitor_memory.sh
```

---

## 🎯 常用操作

### 导入文本
```bash
source venv/bin/activate
python3 knowledge_manager.py import_text "你的文本内容" "标题"
```

### 导入文件
```bash
python3 knowledge_manager.py import_file /path/to/file.pdf
```

### 批量导入目录
```bash
python3 knowledge_manager.py import_dir /path/to/directory
```

### 搜索知识
```bash
python3 knowledge_manager.py search "关键词"
```

### 查看统计
```bash
python3 knowledge_manager.py stats
```

---

## 🔧 故障排查快速命令

### 检查Python版本
```bash
python3 --version
```

### 检查内存使用
```bash
free -h
```

### 检查磁盘空间
```bash
df -h
```

### 查看Python进程
```bash
ps aux | grep python
```

### 清空向量库（内存不足时）
```bash
rm -rf knowledge_vector_db/vector_db.pkl
```

### 使用国内镜像（pip慢时）
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements_knowledge.txt
```

---

## 📊 一键脚本

### 一键部署（克隆+部署+测试）
```bash
cat > deploy_all.sh << 'EOF'
#!/bin/bash
set -e
echo "开始一键部署..."
if [ -d "AIGC_mood" ]; then
    cd AIGC_mood/项目代码 && git pull
else
    git clone https://github.com/UserNewUser456/AIGC_mood.git
    cd AIGC_mood/项目代码
fi
chmod +x deploy_server.sh && ./deploy_server.sh
chmod +x test_on_server.sh && ./test_on_server.sh
echo "部署完成！"
EOF
chmod +x deploy_all.sh && ./deploy_all.sh
```

---

## 🎓 文档索引

| 文档 | 说明 |
|------|------|
| `SERVER_STEP_BY_STEP.md` | 详细部署指南（推荐）|
| `QUICKSTART.md` | 快速开始 |
| `DEPLOYMENT_SUMMARY.md` | 部署总结 |
| `knowledge_manager_README.md` | 使用文档 |
| `INTEGRATION_GUIDE.md` | 集成指南 |

---

## ✅ 部署成功检查清单

- [ ] `./deploy_server.sh` 执行完成
- [ ] `./test_on_server.sh` 所有测试通过
- [ ] 可以成功导入文本
- [ ] 可以成功搜索知识
- [ ] 内存使用率 < 80%
- [ ] 模型加载成功（~80MB）

---

## 💡 提示

1. **网络慢？** 使用国内镜像
2. **内存不足？** 清空向量库，分批导入
3. **需要帮助？** 查看 `SERVER_STEP_BY_STEP.md`

---

**部署遇到问题？详细步骤请查看 `SERVER_STEP_BY_STEP.md`**
