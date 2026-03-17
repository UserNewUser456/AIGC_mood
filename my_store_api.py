"""
商城模块 + 推荐引擎模块
后端工程师B - 任务3、4

功能：
1. 商城API：商品CRUD/分类筛选/关键词搜索/商品详情
2. 推荐引擎：基于用户画像和实时情绪的商品推荐
"""

from flask import Blueprint, request, jsonify
from extensions import db
from datetime import datetime

store_bp = Blueprint('store_b', __name__)

# ==================== 商城API ====================

@store_bp.route('/products', methods=['GET'])
def get_products():
    """
    GET /api/b-store/products - 获取商品列表
    参数: category(分类), keyword(关键词), emotion(适用情绪), page, per_page
    """
    try:
        category = request.args.get('category', '')
        keyword = request.args.get('keyword', '')
        emotion = request.args.get('emotion', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        from models import Resource
        
        query = Resource.query.filter(Resource.type.in_(['product', 'meditation', 'article', 'music']))
        
        if category:
            query = query.filter(Resource.type == category)
        
        if keyword:
            query = query.filter(
                db.or_(
                    Resource.title.ilike(f'%{keyword}%'),
                    Resource.description.ilike(f'%{keyword}%'),
                    Resource.tags.ilike(f'%{keyword}%')
                )
            )
        
        if emotion:
            query = query.filter(Resource.applicable_emotions.ilike(f'%{emotion}%'))
        
        pagination = query.order_by(Resource.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "data": {
                "products": [p.to_dict() for p in pagination.items],
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


@store_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    GET /api/b-store/categories - 获取分类列表
    """
    try:
        from models import Resource
        
        categories = db.session.query(Resource.type).distinct().all()
        
        category_map = {
            'product': '疗愈商品',
            'meditation': '冥想课程',
            'article': '心理文章',
            'music': '疗愈音乐',
            'consultation': '咨询服务'
        }
        
        return jsonify({
            "success": True,
            "data": [
                {"type": c[0], "name": category_map.get(c[0], c[0])}
                for c in categories if c[0]
            ]
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@store_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """
    GET /api/b-store/products/<id> - 获取商品详情
    """
    try:
        from models import Resource
        
        product = Resource.query.get(product_id)
        
        if not product:
            return jsonify({"success": False, "message": "商品不存在"}), 404
        
        return jsonify({
            "success": True,
            "data": product.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@store_bp.route('/products', methods=['POST'])
def create_product():
    """
    POST /api/b-store/products - 创建商品
    请求: {"type": "product", "title": "商品名称", "description": "描述", "url": "链接", "applicable_emotions": "焦虑,压力"}
    """
    try:
        data = request.get_json() or {}
        
        required = ['type', 'title']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "message": f"缺少必要字段: {field}"}), 400
        
        from models import Resource
        
        product = Resource(
            type=data['type'],
            title=data['title'],
            description=data.get('description', ''),
            url=data.get('url', ''),
            applicable_emotions=data.get('applicable_emotions', '')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "商品创建成功",
            "data": product.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@store_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    PUT /api/b-store/products/<id> - 更新商品
    """
    try:
        data = request.get_json() or {}
        
        from models import Resource
        
        product = Resource.query.get(product_id)
        
        if not product:
            return jsonify({"success": False, "message": "商品不存在"}), 404
        
        if 'title' in data:
            product.title = data['title']
        if 'description' in data:
            product.description = data['description']
        if 'url' in data:
            product.url = data['url']
        if 'applicable_emotions' in data:
            product.applicable_emotions = data['applicable_emotions']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "商品更新成功",
            "data": product.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@store_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    DELETE /api/b-store/products/<id> - 删除商品
    """
    try:
        from models import Resource
        
        product = Resource.query.get(product_id)
        
        if not product:
            return jsonify({"success": False, "message": "商品不存在"}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "商品删除成功"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 推荐引擎API ====================

@store_bp.route('/recommend/products', methods=['GET'])
def recommend_products():
    """
    GET /api/b-recommend/products - 基于情绪的商品推荐
    参数: user_id, emotion(当前情绪), limit(默认10)
    """
    try:
        user_id = request.args.get('user_id', 1, type=int)
        emotion = request.args.get('emotion', '平静')
        limit = int(request.args.get('limit', 10))
        
        from models import Resource, EmotionRecord
        
        # 获取用户最近的情绪记录
        recent_emotions = EmotionRecord.query.filter_by(user_id=user_id) \
            .order_by(EmotionRecord.created_at.desc()).limit(10).all()
        
        # 分析用户情绪画像
        emotion_counts = {}
        for r in recent_emotions:
            emotion_counts[r.emotion] = emotion_counts.get(r.emotion, 0) + 1
        
        # 构建推荐查询：优先推荐适合当前情绪和历史情绪的商品
        query = Resource.query.filter(
            Resource.type.in_(['product', 'meditation', 'music'])
        )
        
        # 查找匹配当前情绪或历史积极情绪的资源
        emotions_to_match = [emotion] + list(emotion_counts.keys())
        
        recommendations = []
        for e in emotions_to_match[:5]:
            matched = Resource.query.filter(
                Resource.applicable_emotions.ilike(f'%{e}%')
            ).limit(limit).all()
            recommendations.extend(matched)
        
        # 去重并限制数量
        seen = set()
        unique_recommendations = []
        for r in recommendations:
            if r.id not in seen:
                seen.add(r.id)
                unique_recommendations.append(r.to_dict())
        
        return jsonify({
            "success": True,
            "data": {
                "user_id": user_id,
                "current_emotion": emotion,
                "user_emotion_profile": emotion_counts,
                "recommendations": unique_recommendations[:limit],
                "recommend_type": "emotion_based"
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@store_bp.route('/recommend/knowledge', methods=['GET'])
def recommend_knowledge():
    """
    GET /api/b-recommend/knowledge - 基于情绪的知识推荐
    参数: user_id, emotion
    """
    try:
        user_id = request.args.get('user_id', 1, type=int)
        emotion = request.args.get('emotion', '平静')
        limit = int(request.args.get('limit', 5))
        
        from models import KnowledgeBase
        
        # 匹配当前情绪的知识
        results = KnowledgeBase.query.filter(
            db.or_(
                KnowledgeBase.tags.ilike(f'%{emotion}%'),
                KnowledgeBase.category.ilike(f'%{emotion}%')
            )
        ).limit(limit).all()
        
        return jsonify({
            "success": True,
            "data": {
                "current_emotion": emotion,
                "knowledge": [k.to_dict() for k in results]
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# 注册路由示例（在app.py中）
"""
from my_store_api import store_bp
app.register_blueprint(store_bp, url_prefix='/api/b-store')
"""
