# 知识库管理工具使用指南

## 概述

这是一个**CPU友好版本**的知识库管理工具，无需GPU即可运行。支持：

1. ✅ **文本导入** - 直接导入文本内容
2. ✅ **文件导入** - 支持TXT、PDF、Word、Markdown等格式
3. ✅ **目录批量导入** - 批量导入整个目录的文件
4. ✅ **文本分析** - 自动提取关键词、实体、摘要
5. ✅ **向量检索** - 基于语义相似度的智能搜索

## 技术特点

- **无需GPU**：使用 `paraphrase-multilingual-MiniLM-L12-v2` 模型，适合CPU环境
- **多语言支持**：支持中文、英文等多种语言
- **自动分析**：集成阿里云百炼API进行智能文本分析
- **本地存储**：向量库持久化存储，无需每次重新加载

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements_knowledge.txt
```

### 2. 配置API密钥（可选）

如果需要使用文本分析功能，设置阿里云百炼API密钥：

```bash
# Windows PowerShell
setx DASHSCOPE_API_KEY "your-api-key"

# Linux/Mac
export DASHSCOPE_API_KEY="your-api-key"
```

或者在代码中直接修改：
```python
DASHSCOPE_API_KEY = 'your-api-key'
```

### 3. 首次运行

首次运行时，会自动下载嵌入模型（约400MB），需要联网：

```bash
python knowledge_manager.py stats
```

## 使用方法

### 命令行方式

#### 1. 导入文本

```bash
python knowledge_manager.py import_text "焦虑症是一种常见的精神障碍，表现为过度的担忧和紧张..." "焦虑症介绍"
```

#### 2. 导入单个文件

```bash
# 导入TXT文件
python knowledge_manager.py import_file ./data/anxiety.txt

# 导入PDF文件
python knowledge_manager.py import_file ./data/psychology_book.pdf

# 导入Word文件
python knowledge_manager.py import_file ./data/notes.docx

# 导入Markdown文件
python knowledge_manager.py import_file ./data/article.md
```

#### 3. 批量导入目录

```bash
python knowledge_manager.py import_dir ./data/books
```

这会自动遍历目录及其子目录，导入所有支持的文本文件（TXT、PDF、Word、MD）。

#### 4. 搜索知识

```bash
python knowledge_manager.py search "焦虑症状"
python knowledge_manager.py search "如何缓解抑郁情绪"
```

#### 5. 查看统计信息

```bash
python knowledge_manager.py stats
```

### Python代码方式

```python
from knowledge_manager import KnowledgeManager

# 创建管理器实例
manager = KnowledgeManager()

# 加载已有向量库
manager.load_vector_db()

# 方式1：导入文本
result = manager.import_text(
    text="抑郁症是一种常见的心理疾病...",
    title="抑郁症简介",
    source="心理学教材",
    analyze=True  # 是否进行文本分析
)
print(result)

# 方式2：导入文件
result = manager.import_file(
    file_path="./data/anxiety.pdf",
    analyze=True
)
print(result)

# 方式3：批量导入目录
result = manager.import_directory(
    dir_path="./data/books",
    analyze=True
)
print(result)

# 搜索知识
result = manager.search_knowledge(
    query="焦虑症的治疗方法",
    top_k=3
)
print(result)

# 查看统计
result = manager.get_stats()
print(result)
```

## 文本分析功能

当启用 `analyze=True` 时，系统会自动调用阿里云百炼API分析文本，提取：

- **emotions**: 情绪列表
- **symptoms**: 症状列表
- **treatments**: 治疗方法列表
- **keywords**: 关键词列表
- **summary**: 文本摘要

示例输出：
```json
{
  "success": true,
  "message": "成功导入 5 个文本块",
  "data": {
    "chunks": 5,
    "analyzed": true,
    "analysis": {
      "emotions": ["焦虑", "担忧"],
      "symptoms": ["失眠", "心悸"],
      "treatments": ["认知行为疗法", "药物治疗"],
      "keywords": ["焦虑症", "心理治疗", "自我调节"],
      "summary": "焦虑症是一种常见的精神障碍，表现为过度的担忧和紧张..."
    }
  }
}
```

## 向量检索原理

### 工作流程

1. **文本分块**：将长文本分割成500字左右的小块（可配置）
2. **向量化**：使用SentenceTransformer模型将文本块转换为向量
3. **存储**：将向量存储在本地文件（pickle格式）
4. **检索**：查询时计算相似度，返回最相关的文本块

### 相似度计算

使用余弦相似度计算文本块与查询的相关性：
```
similarity = cosine_similarity(query_vector, document_vector)
```

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| 纯文本 | .txt | UTF-8编码的文本文件 |
| PDF | .pdf | 需要安装pypdf库 |
| Word | .doc, .docx | 需要安装python-docx库 |
| Markdown | .md, .markdown | 支持标准Markdown格式 |

## 配置参数

可在 `knowledge_manager.py` 中修改：

```python
# 嵌入模型（CPU友好）
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'

# 向量库存储路径
VECTOR_DB_PATH = './knowledge_vector_db'

# 文本分块大小
TEXT_CHUNK_SIZE = 500
TEXT_CHUNK_OVERLAP = 100

# 阿里云API配置
DASHSCOPE_API_KEY = 'your-api-key'
```

## 常见问题

### 1. 模型下载慢怎么办？

首次运行需要下载嵌入模型（约400MB），如果速度慢，可以：

- 使用国内镜像（如清华大学源）
- 手动下载模型后放到 `~/.cache/torch/sentence_transformers/`

### 2. 如何更换更快的模型？

可以将 `EMBEDDING_MODEL` 改为：
- `all-MiniLM-L6-v2` - 更小更快
- `paraphrase-multilingual-mpnet-base-v2` - 更准确但更大

### 3. 文本分析失败怎么办？

检查：
- API密钥是否正确
- 网络连接是否正常
- API额度是否充足

可以设置 `analyze=False` 跳过分析，仅进行向量化。

### 4. 向量库文件太大怎么办？

- 减少导入的文本数量
- 增大 `TEXT_CHUNK_SIZE` 减少分块数量
- 定期清理不重要的内容

## 性能优化建议

1. **批量导入**：使用 `import_directory` 而不是逐个导入
2. **控制分块大小**：根据文本特点调整 `TEXT_CHUNK_SIZE`
3. **关闭分析**：如果不需要文本分析，设置 `analyze=False`
4. **定期清理**：删除不需要的知识条目

## 与管理员后台集成

可以将此工具集成到 `admin_server.py` 中：

```python
# 在admin_server.py中添加
from knowledge_manager import KnowledgeManager

# 初始化管理器
knowledge_manager = KnowledgeManager()
knowledge_manager.load_vector_db()

# 添加API路由
@app.route('/api/admin/knowledge/import_text', methods=['POST'])
def import_knowledge_text():
    """导入文本到知识库"""
    data = request.get_json()
    result = knowledge_manager.import_text(
        text=data['text'],
        title=data.get('title', ''),
        source=data.get('source', ''),
        analyze=True
    )
    return jsonify(result)

@app.route('/api/admin/knowledge/search', methods=['GET'])
def search_knowledge():
    """搜索知识"""
    query = request.args.get('q', '')
    result = knowledge_manager.search_knowledge(query)
    return jsonify(result)
```

## 技术支持

如有问题，请检查：
1. Python版本 >= 3.8
2. 所有依赖已正确安装
3. 网络连接正常（首次运行需要下载模型）
4. API密钥配置正确（如使用分析功能）
