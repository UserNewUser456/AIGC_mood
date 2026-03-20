"""
知识库管理扩展 - 集成到管理员后台
基于 knowledge_manager.py 的API接口
"""

from flask import Blueprint, request, jsonify
from knowledge_manager import KnowledgeManager
import os

# 创建蓝图
knowledge_ext_bp = Blueprint('knowledge_ext', __name__)

# 初始化知识库管理器
knowledge_manager = None


def init_knowledge_manager():
    """初始化知识库管理器"""
    global knowledge_manager
    if knowledge_manager is None:
        knowledge_manager = KnowledgeManager()
        knowledge_manager.load_vector_db()
    return knowledge_manager


# ==================== 文本导入接口 ====================

@knowledge_ext_bp.route('/import_text', methods=['POST'])
def import_knowledge_text():
    """
    POST /api/admin/knowledge/import_text
    导入文本到知识库

    请求体:
    {
        "text": "文本内容",
        "title": "标题",
        "source": "来源",
        "analyze": true/false  // 是否进行文本分析（默认true）
    }
    """
    try:
        manager = init_knowledge_manager()

        data = request.get_json() or {}
        text = data.get('text', '').strip()
        title = data.get('title', '').strip()
        source = data.get('source', '').strip()
        analyze = data.get('analyze', True)

        if not text:
            return jsonify({
                'success': False,
                'error': '文本内容不能为空'
            }), 400

        # 导入文本
        result = manager.import_text(
            text=text,
            title=title,
            source=source,
            analyze=analyze
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }), 500


@knowledge_ext_bp.route('/import_file', methods=['POST'])
def import_knowledge_file():
    """
    POST /api/admin/knowledge/import_file
    从文件导入知识

    请求体:
    {
        "file_path": "文件路径",
        "title": "标题（可选，默认使用文件名）",
        "analyze": true/false
    }
    """
    try:
        manager = init_knowledge_manager()

        data = request.get_json() or {}
        file_path = data.get('file_path', '').strip()
        title = data.get('title', '').strip()
        analyze = data.get('analyze', True)

        if not file_path:
            return jsonify({
                'success': False,
                'error': '文件路径不能为空'
            }), 400

        # 导入文件
        result = manager.import_file(
            file_path=file_path,
            title=title,
            analyze=analyze
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }), 500


@knowledge_ext_bp.route('/import_dir', methods=['POST'])
def import_knowledge_directory():
    """
    POST /api/admin/knowledge/import_dir
    批量导入目录

    请求体:
    {
        "dir_path": "目录路径",
        "analyze": true/false
    }
    """
    try:
        manager = init_knowledge_manager()

        data = request.get_json() or {}
        dir_path = data.get('dir_path', '').strip()
        analyze = data.get('analyze', True)

        if not dir_path:
            return jsonify({
                'success': False,
                'error': '目录路径不能为空'
            }), 400

        # 批量导入
        result = manager.import_directory(
            dir_path=dir_path,
            analyze=analyze
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }), 500


# ==================== 知识检索接口 ====================

@knowledge_ext_bp.route('/search', methods=['GET'])
def search_knowledge():
    """
    GET /api/admin/knowledge/search
    搜索知识库

    参数:
    - q: 查询关键词
    - top_k: 返回结果数量（默认3）
    """
    try:
        manager = init_knowledge_manager()

        query = request.args.get('q', '').strip()
        top_k = request.args.get('top_k', 3, type=int)

        if not query:
            return jsonify({
                'success': False,
                'error': '查询关键词不能为空'
            }), 400

        # 搜索知识
        result = manager.search_knowledge(query=query, top_k=top_k)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'搜索失败: {str(e)}'
        }), 500


# ==================== 统计信息接口 ====================

@knowledge_ext_bp.route('/stats', methods=['GET'])
def get_knowledge_stats():
    """
    GET /api/admin/knowledge/stats
    获取知识库统计信息
    """
    try:
        manager = init_knowledge_manager()

        result = manager.get_stats()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取统计信息失败: {str(e)}'
        }), 500


# ==================== 向量库管理接口 ====================

@knowledge_ext_bp.route('/vector_db/save', methods=['POST'])
def save_vector_db():
    """
    POST /api/admin/knowledge/vector_db/save
    保存向量库
    """
    try:
        manager = init_knowledge_manager()
        manager.vector_store.save()

        return jsonify({
            'success': True,
            'message': '向量库保存成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        }), 500


@knowledge_ext_bp.route('/vector_db/load', methods=['POST'])
def load_vector_db():
    """
    POST /api/admin/knowledge/vector_db/load
    加载向量库
    """
    try:
        manager = init_knowledge_manager()
        success = manager.load_vector_db()

        if success:
            return jsonify({
                'success': True,
                'message': '向量库加载成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '向量库加载失败'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'加载失败: {str(e)}'
        }), 500


@knowledge_ext_bp.route('/vector_db/clear', methods=['POST'])
def clear_vector_db():
    """
    POST /api/admin/knowledge/vector_db/clear
    清空向量库（慎用！）
    """
    try:
        manager = init_knowledge_manager()

        # 清空向量库
        manager.vector_store.documents = []
        manager.vector_store.embeddings = []
        manager.vector_store.metadata = []
        manager.import_history = []

        # 保存空向量库
        manager.vector_store.save()

        return jsonify({
            'success': True,
            'message': '向量库已清空'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'清空失败: {str(e)}'
        }), 500


# ==================== 文件上传接口（支持前端直接上传）====================

import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './knowledge_uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@knowledge_ext_bp.route('/upload', methods=['POST'])
def upload_and_import():
    """
    POST /api/admin/knowledge/upload
    上传文件并导入到知识库

    支持multipart/form-data上传
    参数:
    - file: 文件
    - title: 标题（可选）
    - analyze: 是否分析（默认true）
    """
    try:
        manager = init_knowledge_manager()

        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400

        file = request.files['file']

        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '未选择文件'
            }), 400

        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型。支持: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # 保存文件
        filename = secure_filename(file.filename)
        # 添加UUID避免文件名冲突
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        # 获取其他参数
        title = request.form.get('title', '').strip()
        analyze = request.form.get('analyze', 'true').lower() == 'true'

        # 导入文件
        result = manager.import_file(
            file_path=filepath,
            title=title,
            analyze=analyze
        )

        # 删除临时文件
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'上传导入失败: {str(e)}'
        }), 500


# ==================== 使用说明 ====================

"""
在 admin_server.py 中集成此扩展：

1. 导入扩展：
   from knowledge_manager_ext import knowledge_ext_bp, init_knowledge_manager

2. 注册蓝图：
   app.register_blueprint(knowledge_ext_bp, url_prefix='/api/admin/knowledge_ext')

3. 初始化管理器（可选）：
   init_knowledge_manager()

4. 启动服务后，可以使用以下API：

   # 导入文本
   POST /api/admin/knowledge_ext/import_text
   Body: {"text": "...", "title": "标题", "source": "来源"}

   # 导入文件（提供路径）
   POST /api/admin/knowledge_ext/import_file
   Body: {"file_path": "./data/book.pdf", "title": "标题"}

   # 批量导入目录
   POST /api/admin/knowledge_ext/import_dir
   Body: {"dir_path": "./data/books"}

   # 上传文件并导入
   POST /api/admin/knowledge_ext/upload
   FormData: file=<文件>, title=标题, analyze=true

   # 搜索知识
   GET /api/admin/knowledge_ext/search?q=焦虑症&top_k=3

   # 获取统计信息
   GET /api/admin/knowledge_ext/stats

   # 保存向量库
   POST /api/admin/knowledge_ext/vector_db/save

   # 加载向量库
   POST /api/admin/knowledge_ext/vector_db/load

   # 清空向量库
   POST /api/admin/knowledge_ext/vector_db/clear
"""
