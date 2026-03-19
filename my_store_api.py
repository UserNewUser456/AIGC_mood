"""
用户商城API服务
端口: 5003

功能：
1. 商品列表（只显示在售商品）
2. 分类筛选/关键词搜索/商品详情
3. 购物车功能（添加/删除）
4. 支付功能（同步到后台订单）
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import json
import os
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234',
    'database': 'emotion_db',
    'charset': 'utf8mb4'
}

# 后台订单API地址
ADMIN_API_URL = 'http://49.235.105.137:5005'

def get_db():
    return pymysql.connect(**DB_CONFIG)

# ==================== 商品API ====================

@app.route('/api/store/products', methods=['GET'])
def get_products():
    """获取商品列表（只显示在售商品）"""
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 只查询在售商品 is_active = 1
    where = "WHERE is_active = 1"
    params = []
    
    if category:
        where += " AND category = %s"
        params.append(category)
    
    if keyword:
        where += " AND (name LIKE %s OR description LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    # 获取总数
    cursor.execute(f"SELECT COUNT(*) as total FROM products {where}", params)
    total = cursor.fetchone()['total']
    
    # 分页查询
    offset = (page - 1) * per_page
    cursor.execute(f"""
        SELECT id, name, description, price, original_price, image_url, 
               category, stock, healing_tags
        FROM products 
        {where}
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    
    products = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'list': products,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
    })

@app.route('/api/store/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """获取商品详情"""
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s AND is_active = 1", (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        return jsonify({'success': False, 'error': '商品不存在或已下架'}), 404
    
    return jsonify({'success': True, 'data': product})

@app.route('/api/store/categories', methods=['GET'])
def get_categories():
    """获取商品分类"""
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT DISTINCT category FROM products WHERE is_active = 1 AND category IS NOT NULL")
    categories = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'data': [{'category': c['category'], 'name': c['category']} for c in categories]
    })

# ==================== 购物车API ====================

# 内存存储购物车（生产环境建议用Redis）
carts = {}  # {user_id: [{product_id, quantity, product_info}]}

@app.route('/api/store/cart', methods=['GET'])
def get_cart():
    """获取用户购物车"""
    user_id = request.args.get('user_id', type=int) or 0  # 默认user_id=0（匿名）
    
    cart_items = carts.get(user_id, [])
    
    # 计算总金额
    total = sum(item['quantity'] * item['price'] for item in cart_items)
    
    return jsonify({
        'success': True,
        'data': {
            'items': cart_items,
            'total': total,
            'count': len(cart_items)
        }
    })

@app.route('/api/store/cart', methods=['POST'])
def add_to_cart():
    """添加商品到购物车"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'success': False, 'error': '商品ID不能为空'}), 400
    
    # 获取商品信息
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE id = %s AND is_active = 1", (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        return jsonify({'success': False, 'error': '商品不存在或已下架'}), 404
    
    # 添加到购物车
    if user_id not in carts:
        carts[user_id] = []
    
    # 检查是否已存在
    for item in carts[user_id]:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            return jsonify({'success': True, 'message': '购物车数量已更新'})
    
    carts[user_id].append({
        'product_id': product_id,
        'quantity': quantity,
        'name': product['name'],
        'price': product['price'],
        'image_url': product.get('image_url', '')
    })
    
    return jsonify({'success': True, 'message': '已添加到购物车'})

@app.route('/api/store/cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    """从购物车删除商品"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or 0
    
    if user_id in carts:
        carts[user_id] = [item for item in carts[user_id] if item['product_id'] != product_id]
    
    return jsonify({'success': True, 'message': '已从购物车移除'})

@app.route('/api/store/cart', methods=['PUT'])
def update_cart():
    """更新购物车商品数量"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if user_id in carts:
        for item in carts[user_id]:
            if item['product_id'] == product_id:
                if quantity <= 0:
                    carts[user_id].remove(item)
                else:
                    item['quantity'] = quantity
                break
    
    return jsonify({'success': True, 'message': '购物车已更新'})

@app.route('/api/store/cart/clear', methods=['DELETE'])
def clear_cart():
    """清空购物车"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if user_id and user_id in carts:
        carts[user_id] = []
    
    return jsonify({'success': True, 'message': '购物车已清空'})

# ==================== 支付API ====================

@app.route('/api/store/order/create', methods=['POST'])
def create_order():
    """创建订单（模拟支付）"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or 0
    payment_method = data.get('payment_method', 'alipay')  # alipay, wechat, balance
    
    cart_items = carts.get(user_id, [])
    if not cart_items:
        return jsonify({'success': False, 'error': '购物车为空'}), 400
    
    # 计算订单金额
    total_amount = sum(item['quantity'] * item['price'] for item in cart_items)
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. 创建订单
        cursor.execute("""
            INSERT INTO orders (user_id, order_no, total_amount, status, created_at)
            VALUES (%s, %s, %s, 'paid', NOW())
        """, (user_id, order_no, total_amount))
        
        order_id = cursor.lastrowid
        
        # 2. 记录订单商品（如果有order_items表）
        # 这里简化处理，直接更新库存
        for item in cart_items:
            cursor.execute("""
                UPDATE products SET stock = stock - %s 
                WHERE id = %s AND stock >= %s
            """, (item['quantity'], item['product_id'], item['quantity']))
        
        conn.commit()
        conn.close()
        
        # 清空购物车
        carts[user_id] = []
        
        return jsonify({
            'success': True,
            'data': {
                'order_id': order_id,
                'order_no': order_no,
                'total_amount': total_amount,
                'status': 'paid',
                'message': '支付成功'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'订单创建失败: {str(e)}'}), 500

@app.route('/api/store/orders', methods=['GET'])
def get_user_orders():
    """获取用户订单列表"""
    user_id = request.args.get('user_id', type=int) or 0
    
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT * FROM orders 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 50
    """, (user_id,))
    orders = cursor.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'data': orders})

# ==================== 健康检查 ====================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'store-api'})

if __name__ == '__main__':
    print("=" * 50)
    print("用户商城服务")
    print("端口: 5006")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5003, debug=True)
