"""
RAG知识库模块
后端工程师B - 任务5

功能：
1. 知识库管理API（增删改查）
2. 知识检索API
"""

from flask import Blueprint, request, jsonify
from extensions import db
from datetime import datetime

knowledge_bp = Blueprint('knowledge_b', __name__)

# ==================== 知识库检索API ====================

@knowledge_bp.route('', methods=['GET'])
def search_knowledge():
    """
    GET /api/b-knowledge - 搜索心理知识
    参数: keyword(关键词), category(分类), page, per_page
    """
    try:
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        from models import KnowledgeBase
        
        query = KnowledgeBase.query
        
        if keyword:
            query = query.filter(
                db.or_(
                    KnowledgeBase.title.ilike(f'%{keyword}%'),
                    KnowledgeBase.content.ilike(f'%{keyword}%'),
                    KnowledgeBase.tags.ilike(f'%{keyword}%')
                )
            )
        
        if category:
            query = query.filter(KnowledgeBase.category == category)
        
        pagination = query.order_by(KnowledgeBase.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "data": {
                "articles": [k.to_dict() for k in pagination.items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages
                }
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@knowledge_bp.route('/search', methods=['GET'])
def knowledge_search():
    """
    GET /api/b-knowledge/search - 搜索知识（别名）
    """
    return search_knowledge()


@knowledge_bp.route('/categories', methods=['GET'])
def get_knowledge_categories():
    """
    GET /api/b-knowledge/categories - 获取知识分类
    """
    try:
        from models import KnowledgeBase
        
        categories = db.session.query(KnowledgeBase.category).distinct().all()
        
        return jsonify({
            "success": True,
            "data": [{"category": c[0]} for c in categories if c[0]]
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@knowledge_bp.route('/<int:knowledge_id>', methods=['GET'])
def get_knowledge_detail(knowledge_id):
    """
    GET /api/b-knowledge/<id> - 获取知识详情
    """
    try:
        from models import KnowledgeBase
        
        knowledge = KnowledgeBase.query.get(knowledge_id)
        
        if not knowledge:
            return jsonify({"success": False, "message": "知识条目不存在"}), 404
        
        return jsonify({
            "success": True,
            "data": knowledge.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 知识库管理API ====================

@knowledge_bp.route('', methods=['POST'])
def create_knowledge():
    """
    POST /api/b-knowledge - 创建知识条目
    请求: {"category": "情绪管理", "title": "标题", "content": "内容", "tags": "标签", "source": "来源"}
    """
    try:
        data = request.get_json() or {}
        
        required = ['category', 'title', 'content']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "message": f"缺少必要字段: {field}"}), 400
        
        from models import KnowledgeBase
        
        knowledge = KnowledgeBase(
            category=data['category'],
            title=data['title'],
            content=data['content'],
            tags=data.get('tags', ''),
            source=data.get('source', '')
        )
        
        db.session.add(knowledge)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "知识条目创建成功",
            "data": knowledge.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@knowledge_bp.route('/<int:knowledge_id>', methods=['PUT'])
def update_knowledge(knowledge_id):
    """
    PUT /api/b-knowledge/<id> - 更新知识条目
    """
    try:
        data = request.get_json() or {}
        
        from models import KnowledgeBase
        
        knowledge = KnowledgeBase.query.get(knowledge_id)
        
        if not knowledge:
            return jsonify({"success": False, "message": "知识条目不存在"}), 404
        
        if 'category' in data:
            knowledge.category = data['category']
        if 'title' in data:
            knowledge.title = data['title']
        if 'content' in data:
            knowledge.content = data['content']
        if 'tags' in data:
            knowledge.tags = data['tags']
        if 'source' in data:
            knowledge.source = data['source']
        
        knowledge.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "知识条目更新成功",
            "data": knowledge.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@knowledge_bp.route('/<int:knowledge_id>', methods=['DELETE'])
def delete_knowledge(knowledge_id):
    """
    DELETE /api/b-knowledge/<id> - 删除知识条目
    """
    try:
        from models import KnowledgeBase
        
        knowledge = KnowledgeBase.query.get(knowledge_id)
        
        if not knowledge:
            return jsonify({"success": False, "message": "知识条目不存在"}), 404
        
        db.session.delete(knowledge)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "知识条目删除成功"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 批量操作 ====================

@knowledge_bp.route('/batch', methods=['POST'])
def batch_create_knowledge():
    """
    POST /api/b-knowledge/batch - 批量创建知识条目
    请求: {"items": [{"category": "...", "title": "...", "content": "..."}, ...]}
    """
    try:
        data = request.get_json() or {}
        items = data.get('items', [])
        
        if not items:
            return jsonify({"success": False, "message": "没有要创建的知识条目"}), 400
        
        from models import KnowledgeBase
        
        created = []
        for item in items:
            if item.get('category') and item.get('title') and item.get('content'):
                knowledge = KnowledgeBase(
                    category=item['category'],
                    title=item['title'],
                    content=item['content'],
                    tags=item.get('tags', ''),
                    source=item.get('source', '')
                )
                db.session.add(knowledge)
                created.append(item['title'])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"成功创建 {len(created)} 个知识条目",
            "data": {"created": created}
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# 注册路由示例（在app.py中）
"""
from my_knowledge_api import knowledge_bp
app.register_blueprint(knowledge_bp, url_prefix='/api/b-knowledge')
"""
