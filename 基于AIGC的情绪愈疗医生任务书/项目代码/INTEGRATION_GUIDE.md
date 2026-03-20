# 知识库管理工具 - 管理员后台集成指南

## 问题说明

您之前在管理员后台的知识库管理中遇到以下问题：

1. ❌ **导入文本出现错误** - 原有实现依赖Ollama，需要GPU
2. ❌ **无法导入书籍** - 缺少文件路径导入功能
3. ❌ **文本分析失败** - 没有适合CPU环境的分析方案

## 解决方案

我为您创建了一套完整的CPU友好型知识库管理解决方案，包含以下文件：

```
├── knowledge_manager.py          # 核心知识库管理工具
├── knowledge_manager_ext.py      # 管理员后台API扩展
├── test_knowledge_manager.py     # 测试脚本
├── requirements_knowledge.txt    # 依赖列表
├── knowledge_manager_README.md   # 详细使用文档
└── INTEGRATION_GUIDE.md          # 本文件（集成指南）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_knowledge.txt
```

### 2. 测试功能

```bash
# 运行测试脚本
python test_knowledge_manager.py
```

### 3. 集成到管理员后台

#### 步骤1：修改 admin_server.py

在 `admin_server.py` 文件顶部添加：

```python
# 导入知识库管理扩展
from knowledge_manager_ext import knowledge_ext_bp, init_knowledge_manager

# 初始化知识库管理器
init_knowledge_manager()
```

#### 步骤2：注册蓝图

在 `admin_server.py` 中注册新的蓝图（在 `app.run()` 之前）：

```python
# 注册知识库扩展蓝图
app.register_blueprint(knowledge_ext_bp, url_prefix='/api/admin/knowledge_ext')
```

#### 步骤3：重启服务

```bash
python admin_server.py
```

## 新增API接口

集成后，管理员后台将拥有以下新接口：

### 1. 文本导入

```bash
# 导入文本内容
POST /api/admin/knowledge_ext/import_text
Content-Type: application/json

{
  "text": "焦虑症是一种常见的精神障碍...",
  "title": "焦虑症介绍",
  "source": "心理学教材",
  "analyze": true
}
```

### 2. 文件导入（通过路径）

```bash
# 导入本地文件
POST /api/admin/knowledge_ext/import_file
Content-Type: application/json

{
  "file_path": "./data/books/anxiety.pdf",
  "title": "焦虑症详解",
  "analyze": true
}
```

### 3. 目录批量导入

```bash
# 批量导入整个目录
POST /api/admin/knowledge_ext/import_dir
Content-Type: application/json

{
  "dir_path": "./data/psychology_books",
  "analyze": true
}
```

### 4. 文件上传导入

```bash
# 通过前端上传文件
POST /api/admin/knowledge_ext/upload
Content-Type: multipart/form-data

file: <选择文件>
title: "心理学书籍"
analyze: true
```

### 5. 知识搜索

```bash
# 搜索知识
GET /api/admin/knowledge_ext/search?q=焦虑症状&top_k=3
```

### 6. 统计信息

```bash
# 获取统计信息
GET /api/admin/knowledge_ext/stats
```

### 7. 向量库管理

```bash
# 保存向量库
POST /api/admin/knowledge_ext/vector_db/save

# 加载向量库
POST /api/admin/knowledge_ext/vector_db/load

# 清空向量库
POST /api/admin/knowledge_ext/vector_db/clear
```

## 前端集成示例

### 1. 导入文本

```javascript
// 导入文本
async function importText(text, title, source) {
  const response = await fetch('http://localhost:5005/api/admin/knowledge_ext/import_text', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      text: text,
      title: title,
      source: source,
      analyze: true
    })
  });

  return await response.json();
}
```

### 2. 上传文件

```javascript
// 上传文件
async function uploadFile(file, title) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('analyze', 'true');

  const response = await fetch('http://localhost:5005/api/admin/knowledge_ext/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  return await response.json();
}
```

### 3. 搜索知识

```javascript
// 搜索知识
async function searchKnowledge(query) {
  const response = await fetch(
    `http://localhost:5005/api/admin/knowledge_ext/search?q=${encodeURIComponent(query)}&top_k=3`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  return await response.json();
}
```

## 管理员后台页面更新

### 知识库管理页面示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>知识库管理</title>
    <style>
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .input-group { margin-bottom: 15px; }
        textarea { width: 100%; height: 150px; padding: 10px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .result { margin-top: 15px; padding: 10px; background: #f8f9fa; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h1>知识库管理</h1>

        <!-- 导入文本 -->
        <div class="section">
            <h2>导入文本</h2>
            <div class="input-group">
                <label>标题：</label>
                <input type="text" id="textTitle" style="width: 100%; padding: 8px;">
            </div>
            <div class="input-group">
                <label>来源：</label>
                <input type="text" id="textSource" style="width: 100%; padding: 8px;">
            </div>
            <div class="input-group">
                <label>内容：</label>
                <textarea id="textContent"></textarea>
            </div>
            <button onclick="importText()">导入</button>
            <div id="textResult" class="result"></div>
        </div>

        <!-- 上传文件 -->
        <div class="section">
            <h2>上传文件</h2>
            <div class="input-group">
                <label>文件：</label>
                <input type="file" id="fileInput" accept=".txt,.pdf,.doc,.docx,.md">
            </div>
            <div class="input-group">
                <label>标题（可选）：</label>
                <input type="text" id="fileTitle" style="width: 100%; padding: 8px;">
            </div>
            <button onclick="uploadFile()">上传</button>
            <div id="fileResult" class="result"></div>
        </div>

        <!-- 搜索知识 -->
        <div class="section">
            <h2>搜索知识</h2>
            <div class="input-group">
                <input type="text" id="searchQuery" style="width: 100%; padding: 8px;" placeholder="输入关键词...">
            </div>
            <button onclick="searchKnowledge()">搜索</button>
            <div id="searchResult" class="result"></div>
        </div>

        <!-- 统计信息 -->
        <div class="section">
            <h2>统计信息</h2>
            <button onclick="getStats()">刷新统计</button>
            <div id="statsResult" class="result"></div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:5005/api/admin/knowledge_ext';
        const token = localStorage.getItem('admin_token');

        // 导入文本
        async function importText() {
            const text = document.getElementById('textContent').value;
            const title = document.getElementById('textTitle').value;
            const source = document.getElementById('textSource').value;

            if (!text) {
                showResult('textResult', '请输入文本内容', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/import_text`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ text, title, source, analyze: true })
                });

                const result = await response.json();
                showResult('textResult', JSON.stringify(result, null, 2),
                          result.success ? 'success' : 'error');
            } catch (error) {
                showResult('textResult', `错误: ${error.message}`, 'error');
            }
        }

        // 上传文件
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            const title = document.getElementById('fileTitle').value;

            if (!file) {
                showResult('fileResult', '请选择文件', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            if (title) formData.append('title', title);
            formData.append('analyze', 'true');

            try {
                const response = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                const result = await response.json();
                showResult('fileResult', JSON.stringify(result, null, 2),
                          result.success ? 'success' : 'error');
            } catch (error) {
                showResult('fileResult', `错误: ${error.message}`, 'error');
            }
        }

        // 搜索知识
        async function searchKnowledge() {
            const query = document.getElementById('searchQuery').value;

            if (!query) {
                showResult('searchResult', '请输入查询关键词', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&top_k=3`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                const result = await response.json();
                showResult('searchResult', JSON.stringify(result, null, 2),
                          result.success ? 'success' : 'error');
            } catch (error) {
                showResult('searchResult', `错误: ${error.message}`, 'error');
            }
        }

        // 获取统计信息
        async function getStats() {
            try {
                const response = await fetch(`${API_BASE}/stats`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                const result = await response.json();
                showResult('statsResult', JSON.stringify(result, null, 2),
                          result.success ? 'success' : 'error');
            } catch (error) {
                showResult('statsResult', `错误: ${error.message}`, 'error');
            }
        }

        // 显示结果
        function showResult(elementId, message, type) {
            const element = document.getElementById(elementId);
            element.innerHTML = `<pre class="${type}">${message}</pre>`;
        }

        // 页面加载时获取统计
        window.onload = function() {
            getStats();
        };
    </script>
</body>
</html>
```

## 与原有知识库功能对比

| 功能 | 原有实现 | 新实现 |
|------|---------|--------|
| 文本导入 | ❌ 经常失败 | ✅ 稳定可靠 |
| 文件导入 | ❌ 不支持 | ✅ 支持多格式 |
| 书籍导入 | ❌ 不支持 | ✅ 支持路径导入 |
| 批量导入 | ❌ 不支持 | ✅ 支持目录导入 |
| 文本分析 | ❌ 依赖Ollama | ✅ 使用API |
| 向量化 | ❌ 需要GPU | ✅ CPU友好 |
| 搜索功能 | ✅ 有 | ✅ 更准确 |
| 统计信息 | ✅ 有 | ✅ 更详细 |

## 常见问题

### 1. 模型下载慢怎么办？

首次运行会下载 `paraphrase-multilingual-MiniLM-L12-v2` 模型（约400MB），可以：

- 使用国内镜像
- 手动下载后放到 `~/.cache/torch/sentence_transformers/`

### 2. 如何禁用文本分析？

设置 `analyze: false` 可以跳过文本分析，只进行向量化：

```json
{
  "text": "...",
  "analyze": false
}
```

### 3. 向量库存储在哪里？

默认存储在 `./knowledge_vector_db/vector_db.pkl`

### 4. 如何清空知识库？

调用 `POST /api/admin/knowledge_ext/vector_db/clear` 接口

## 技术支持

如有问题，请参考：

1. `knowledge_manager_README.md` - 详细使用文档
2. `test_knowledge_manager.py` - 测试示例
3. 运行测试脚本验证功能是否正常

## 总结

这套解决方案完全解决了您的问题：

✅ **文本导入稳定** - 不依赖Ollama，使用CPU友好的SentenceTransformer
✅ **支持书籍导入** - 可以通过文件路径或上传方式导入各种格式
✅ **文本分析可用** - 使用阿里云百炼API进行分析，无需本地GPU
✅ **批量导入** - 支持导入整个目录的知识文件
✅ **易于集成** - 提供完整的REST API和前端示例

现在您可以安全地在管理员后台管理知识库了！
