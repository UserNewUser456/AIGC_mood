# -*- coding: utf-8 -*-
"""
文档知识提取API测试脚本
"""
import requests
import json
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://49.235.105.137:5002"

def test_health():
    """测试健康检查"""
    print("\n1. 健康检查 /health")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_process_text():
    """测试文本处理"""
    print("\n2. 测试文本处理 /api/document/process-text")
    print("-" * 40)
    
    sample_text = """
    心理咨询是一种帮助人们解决心理问题、维护心理健康的专业服务。
    心理咨询师通过与来访者的对话，帮助他们了解自己的情绪、行为和思维模式。
    
    常见的心理咨询方法包括认知行为疗法、精神分析疗法、人本主义疗法等。
    认知行为疗法是一种常用的心理治疗方法，主要通过改变来访者的负面思维模式来改善情绪和行为。
    
    焦虑症是一种常见的心理障碍，表现为持续的担忧、紧张和恐惧。
    焦虑症的症状包括心慌、出汗、颤抖、注意力难以集中等。
    治疗方法包括药物治疗、心理治疗和生活方式调整。
    
    抑郁症是一种情绪障碍，主要表现为持续的情绪低落、兴趣丧失和精力不足。
    抑郁症可能影响一个人的感受、思考和日常活动。
    """
    
    data = {
        "text": sample_text,
        "name": "心理咨询基础知识",
        "category": "心理健康"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/document/process-text",
            json=data,
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            data = result.get('data', {})
            print(f"文档名称: {data.get('doc_name')}")
            print(f"总字符数: {data.get('total_chars')}")
            print(f"总块数: {data.get('total_chunks')}")
            print(f"关键词: {data.get('keywords')}")
            print(f"摘要: {data.get('summary', '')[:100]}...")
            print(f"知识提取: {data.get('knowledge_extracted')}")
        else:
            print(f"处理失败: {result.get('error')}")
        
        return result.get('success', False)
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def test_search():
    """测试知识搜索"""
    print("\n3. 测试知识搜索 /api/document/search")
    print("-" * 40)
    
    queries = ["焦虑", "抑郁症", "心理咨询"]
    
    for query in queries:
        print(f"\n搜索关键词: {query}")
        try:
            response = requests.get(
                f"{BASE_URL}/api/document/search",
                params={"q": query, "top_k": 3},
                timeout=10
            )
            print(f"状态码: {response.status_code}")
            result = response.json()
            
            if result.get('success'):
                data = result.get('data', [])
                print(f"找到 {len(data)} 条结果")
                for i, item in enumerate(data[:2], 1):
                    print(f"  结果{i}: {item.get('doc_name', 'N/A')}")
                    print(f"    来源: {item.get('source', 'N/A')}")
                    print(f"    内容: {str(item.get('content', ''))[:80]}...")
            else:
                print(f"搜索失败: {result.get('error')}")
        except Exception as e:
            print(f"请求失败: {e}")


def test_list_documents():
    """测试文档列表"""
    print("\n4. 测试文档列表 /api/document/list")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/document/list", timeout=10)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            data = result.get('data', [])
            print(f"共有 {len(data)} 个文档")
            for doc in data:
                print(f"  - {doc.get('name')} ({doc.get('category')})")
        else:
            print(f"获取失败: {result.get('error')}")
        
        return result.get('success', False)
    except Exception as e:
        print(f"请求失败: {e}")
        return False


def main():
    print("="*60)
    print("文档知识提取API测试")
    print("="*60)
    print(f"服务器地址: {BASE_URL}")
    
    results = {
        "健康检查": test_health(),
        "文本处理": test_process_text(),
        "文档列表": test_list_documents()
    }
    
    test_search()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, success in results.items():
        status = "通过" if success else "失败"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
