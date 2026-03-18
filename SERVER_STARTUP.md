# 服务器启动指南

## 手动启动步骤

### 1. 连接到服务器
```bash
ssh root@49.235.105.137
# 密码: 20040105Jjq
```

### 2. 启动Neo4j
```bash
neo4j start
# 等待几秒
neo4j status
```

### 3. 启动管理员后台 (端口5005)
```bash
cd /root/AIGC_mood
python3 admin_server.py
```

### 4. 启动RAG知识图谱服务 (端口5001)
```bash
cd /root/AIGC_mood
python3 my_rag_knowledge_api.py
```

### 5. 测试API

在本地Windows上运行测试脚本:
```cmd
python test_rag_api.py
```

## API测试端点

- 健康检查: http://49.235.105.137:5001/health
- 情绪列表: http://49.235.105.137:5001/api/rag-knowledge/emotions
- 情绪知识: http://49.235.105.137:5001/api/rag-knowledge/emotion/焦虑
- 搜索: http://49.235.105.137:5001/api/rag-knowledge/search?keyword=焦虑
- 图谱统计: http://49.235.105.137:5001/api/rag-knowledge/graph-stats
- 对话: POST http://49.235.105.137:5001/api/rag-knowledge/chat

## 使用Docker启动Neo4j (备选方案)

如果neo4j命令不可用:
```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/root1234 \
  neo4j:latest
```
