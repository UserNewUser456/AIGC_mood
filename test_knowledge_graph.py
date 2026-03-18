"""
知识图谱功能测试脚本
使用方法: python test_knowledge_graph.py
"""
import requests
import json

# 服务地址
ADMIN_BASE = "http://localhost:5005"
RAG_BASE = "http://localhost:5001"

# 测试用的管理员账号（需先在数据库创建）
TEST_ADMIN = {"username": "admin", "password": "admin123"}

def test_health():
    """测试服务健康状态"""
    print("\n=== 1. 健康检查 ===")
    
    # Admin服务
    try:
        r = requests.get(f"{ADMIN_BASE}/health", timeout=5)
        print(f"Admin服务: {r.json()}")
    except Exception as e:
        print(f"Admin服务连接失败: {e}")
    
    # RAG服务
    try:
        r = requests.get(f"{RAG_BASE}/health", timeout=5)
        print(f"RAG服务: {r.json()}")
    except Exception as e:
        print(f"RAG服务连接失败: {e}")

def test_admin_login():
    """测试管理员登录"""
    print("\n=== 2. 管理员登录 ===")
    
    try:
        r = requests.post(
            f"{ADMIN_BASE}/api/admin/login",
            json=TEST_ADMIN,
            timeout=10
        )
        data = r.json()
        print(f"登录结果: {data}")
        
        if data.get('success'):
            token = data['data']['token']
            print(f"获取Token成功: {token[:20]}...")
            return token
    except Exception as e:
        print(f"登录失败: {e}")
    
    return None

def test_knowledge_import(token):
    """测试知识导入功能"""
    print("\n=== 3. 知识导入测试 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试文本
    test_text = """
    焦虑是一种常见的情绪反应，当人们面临压力、不确定性或潜在威胁时会出现。
    焦虑可能导致心慌、肌肉紧张、注意力难以集中等身体症状。
    可以通过正念冥想、深呼吸练习和认知行为疗法来缓解焦虑情绪。
    4-7-8呼吸法是一种有效的放松技巧：吸气4秒，屏息7秒，呼气8秒。
    """
    
    try:
        r = requests.post(
            f"{ADMIN_BASE}/api/admin/knowledge/import",
            json={
                "title": "焦虑情绪知识测试",
                "source": "测试导入",
                "text": test_text
            },
            headers=headers,
            timeout=60
        )
        data = r.json()
        print(f"导入结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"导入失败: {e}")

def test_knowledge_graph(token):
    """测试知识图谱查询"""
    print("\n=== 4. 知识图谱查询 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 获取图谱统计
        r = requests.get(
            f"{ADMIN_BASE}/api/admin/knowledge/stats",
            headers=headers,
            timeout=10
        )
        print(f"图谱统计: {r.json()}")
        
        # 获取图谱可视化数据
        r = requests.get(
            f"{ADMIN_BASE}/api/admin/knowledge/graph",
            headers=headers,
            timeout=10
        )
        data = r.json()
        if data.get('success'):
            nodes = data['data'].get('nodes', [])
            links = data['data'].get('links', [])
            print(f"图谱节点数: {len(nodes)}, 关系数: {len(links)}")
    except Exception as e:
        print(f"查询失败: {e}")

def test_rag_chat():
    """测试RAG对话功能"""
    print("\n=== 5. RAG智能对话测试 ===")
    
    test_questions = [
        "我最近总是感到焦虑该怎么办？",
        "失眠有什么治疗方法吗？",
        "心情不好的时候有什么技巧可以缓解？"
    ]
    
    for q in test_questions:
        print(f"\n问题: {q}")
        try:
            r = requests.post(
                f"{RAG_BASE}/api/rag-knowledge/chat",
                json={"question": q},
                timeout=30
            )
            data = r.json()
            if data.get('success'):
                answer = data['data'].get('answer', '')[:200]
                emotion = data['data'].get('emotion')
                print(f"检测情绪: {emotion}")
                print(f"回答: {answer}...")
        except Exception as e:
            print(f"请求失败: {e}")

def test_rag_search():
    """测试RAG搜索功能"""
    print("\n=== 6. RAG知识搜索 ===")
    
    keywords = ["焦虑", "抑郁", "治疗"]
    
    for kw in keywords:
        try:
            r = requests.get(
                f"{RAG_BASE}/api/rag-knowledge/search",
                params={"keyword": kw},
                timeout=10
            )
            data = r.json()
            if data.get('success'):
                items = data['data']
                print(f"关键词'{kw}'找到 {len(items)} 条结果")
        except Exception as e:
            print(f"搜索'{kw}'失败: {e}")

def main():
    print("="*50)
    print("知识图谱功能测试")
    print("="*50)
    
    # 1. 健康检查
    test_health()
    
    # 2. 管理员登录
    token = test_admin_login()
    if not token:
        print("警告: 无法登录，跳过需要认证的测试")
        return
    
    # 3. 知识导入测试
    test_knowledge_import(token)
    
    # 4. 知识图谱查询
    test_knowledge_graph(token)
    
    # 5. RAG对话测试
    test_rag_chat()
    
    # 6. RAG搜索测试
    test_rag_search()
    
    print("\n" + "="*50)
    print("测试完成")
    print("="*50)

if __name__ == "__main__":
    main()
