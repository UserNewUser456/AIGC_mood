# 服务器部署指南

## 当前状态
- 代码已上传到Git仓库 ✅
- SSH连接暂时不可用
- 需要手动在服务器上执行部署命令

## 手动部署步骤

### 方法1: 使用PuTTY或终端连接服务器

1. 连接到服务器:
   ```
   ssh root@49.235.105.137
   密码: 20040105Jjq
   ```

2. 进入项目目录并拉取代码:
   ```bash
   cd /root/AIGC_mood
   git pull origin master
   ```

3. 安装依赖:
   ```bash
   pip install PyPDF2 python-docx langchain langchain-community
   ```

4. 启动服务:
   ```bash
   # 启动Neo4j
   neo4j start

   # 启动管理员后台 (端口5005)
   nohup python3 admin_server.py > /tmp/admin.log 2>&1 &

   # 启动RAG知识图谱服务 (端口5001)
   nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &

   # 启动文档知识API服务 (端口5002)
   nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &
   ```

5. 检查服务状态:
   ```bash
   netstat -tlnp | grep -E ':(5001|5002|5005)'
   ```

### 方法2: 使用Windows命令行

双击运行 `deploy_server.bat` 文件（如果SSH可用）

## 服务地址

部署完成后，服务地址如下:

| 服务 | 地址 |
|------|------|
| 管理员后台 | http://49.235.105.137:5005 |
| RAG知识图谱API | http://49.235.105.137:5001 |
| 文档知识API | http://49.235.105.137:5002 |

## 测试API

### 1. 测试RAG知识图谱API
```bash
curl -X POST http://49.235.105.137:5001/api/rag-knowledge/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "我最近很焦虑怎么办？"}'
```

### 2. 测试文档知识API
```bash
curl -X POST http://49.235.105.137:5002/api/document/process-text \
  -H "Content-Type: application/json" \
  -d '{"text": "心理咨询是帮助人们解决心理问题的专业服务。焦虑症是一种常见的心理障碍。", "name": "心理知识", "category": "心理学"}'
```

### 3. 搜索知识
```bash
curl "http://49.235.105.137:5002/api/document/search?q=焦虑"
```

## 新增功能说明

### 文档知识API功能

1. **文档上传** (`/api/document/upload`)
   - 支持PDF、Word(.docx)、TXT格式
   - 自动提取关键词和摘要
   - 存储到Neo4j知识图谱

2. **文本处理** (`/api/document/process-text`)
   - 直接提交文本内容
   - 自动分割成块
   - 提取关键词和摘要
   - 存储到知识图谱

3. **知识搜索** (`/api/document/search`)
   - 关键词搜索
   - 向量相似度检索

4. **文档管理**
   - 列出所有文档: `/api/document/list`
   - 获取文档详情: `/api/document/<doc_id>`
   - 删除文档: `/api/document/<doc_id>` (DELETE)
