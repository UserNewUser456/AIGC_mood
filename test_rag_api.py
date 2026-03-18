"""
RAG知识图谱API测试脚本
用于测试my_rag_knowledge_api.py的对话功能
"""
import requests
import json
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 服务器地址
BASE_URL = "http://49.235.105.137:5001"

def test_health():
    """测试健康检查接口"""
    print("\n" + "="*50)
    print("1. 测试健康检查接口 /health")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_emotions():
    """测试获取所有情绪类型"""
    print("\n" + "="*50)
    print("2. 测试获取所有情绪 /api/rag-knowledge/emotions")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/api/rag-knowledge/emotions", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_emotion_knowledge():
    """测试获取特定情绪的知识"""
    print("\n" + "="*50)
    print("3. 测试获取焦虑情绪的知识 /api/rag-knowledge/emotion/焦虑")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/api/rag-knowledge/emotion/焦虑", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_search():
    """测试搜索知识"""
    print("\n" + "="*50)
    print("4. 测试搜索知识 /api/rag-knowledge/search?keyword=焦虑")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/api/rag-knowledge/search?keyword=焦虑", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_graph_stats():
    """测试知识图谱统计"""
    print("\n" + "="*50)
    print("5. 测试知识图谱统计 /api/rag-knowledge/graph-stats")
    print("="*50)
    try:
        response = requests.get(f"{BASE_URL}/api/rag-knowledge/graph-stats", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_chat():
    """测试对话接口"""
    print("\n" + "="*50)
    print("6. 测试对话接口 /api/rag-knowledge/chat")
    print("="*50)
    
    test_questions = [
        {"question": "我最近总是感到焦虑，怎么办？"},
        {"question": "失眠怎么办？"},
        {"question": "心情不好，感觉很抑郁"}
    ]
    
    for i, q in enumerate(test_questions, 1):
        print(f"\n--- 测试问题 {i}: {q['question']} ---")
        try:
            response = requests.post(
                f"{BASE_URL}/api/rag-knowledge/chat",
                json=q,
                timeout=30
            )
            print(f"状态码: {response.status_code}")
            data = response.json()
            print(f"检测情绪: {data.get('data', {}).get('emotion', 'N/A')}")
            print(f"风险等级: {data.get('data', {}).get('risk_level', 'N/A')}")
            print(f"回答: {data.get('data', {}).get('answer', 'N/A')[:200]}...")
            print(f"知识条目数: {len(data.get('data', {}).get('knowledge_items', []))}")
        except Exception as e:
            print(f"请求失败: {e}")

def main():
    print("="*60)
    print("RAG知识图谱API测试")
    print("="*60)
    print(f"服务器地址: {BASE_URL}")
    
    # 先测试各个接口
    results = {
        "健康检查": test_health(),
        "获取情绪列表": test_emotions(),
        "获取情绪知识": test_emotion_knowledge(),
        "搜索知识": test_search(),
        "图谱统计": test_graph_stats()
    }
    
    # 测试对话接口
    test_chat()
    
    # 总结
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

if __name__ == "__main__":
    main()
