# Final API Test
import requests
import json

print("=== 测试API服务 ===\n")

# 测试1: RAG API 健康检查
print("1. RAG API (5001) 健康检查")
try:
    r = requests.get("http://49.235.105.137:5001/health", timeout=10)
    print(f"   状态: {r.json()}\n")
except Exception as e:
    print(f"   错误: {e}\n")

# 测试2: 文档API 健康检查
print("2. 文档API (5002) 健康检查")
try:
    r = requests.get("http://49.235.105.137:5002/health", timeout=10)
    print(f"   状态: {r.json()}\n")
except Exception as e:
    print(f"   错误: {e}\n")

# 测试3: 管理员API 健康检查
print("3. 管理员API (5005) 健康检查")
try:
    r = requests.get("http://49.235.105.137:5005/health", timeout=10)
    print(f"   状态: {r.json()}\n")
except Exception as e:
    print(f"   错误: {e}\n")

# 测试4: 文档知识提取
print("4. 文档知识提取测试")
data = {
    "text": "心理咨询是帮助人们解决心理问题的专业服务。焦虑症是一种常见的心理健康问题，表现为持续的紧张和担忧。治疗方法包括认知行为疗法和正念冥想。",
    "name": "心理健康知识",
    "category": "心理学"
}
try:
    r = requests.post("http://49.235.105.137:5002/api/document/process-text", 
                     json=data, timeout=30)
    result = r.json()
    print(f"   成功: {result.get('success')}")
    print(f"   关键词数: {result.get('keywords_count', 0)}")
    print(f"   文档块数: {result.get('chunks_count', 0)}\n")
except Exception as e:
    print(f"   错误: {e}\n")

# 测试5: RAG对话
print("5. RAG对话测试")
data = {"question": "我最近很焦虑怎么办"}
try:
    r = requests.post("http://49.235.105.137:5001/api/rag-knowledge/chat",
                     json=data, timeout=30)
    result = r.json()
    if result.get('success'):
        print(f"   情绪: {result['data'].get('emotion')}")
        print(f"   回答: {result['data'].get('answer', '')[:100]}...")
except Exception as e:
    print(f"   错误: {e}")

print("\n=== 测试完成 ===")
