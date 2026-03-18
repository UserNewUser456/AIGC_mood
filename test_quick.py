# Quick API Test with longer timeout
import requests

# 测试1: RAG对话
print("测试RAG对话...")
try:
    r = requests.post("http://49.235.105.137:5001/api/rag-knowledge/chat",
                     json={"question": "我最近很焦虑怎么办"}, timeout=60)
    result = r.json()
    if result.get('success'):
        print(f"情绪: {result['data'].get('emotion')}")
        print(f"回答: {result['data'].get('answer', '')[:80]}...")
    else:
        print(f"失败: {result}")
except Exception as e:
    print(f"错误: {e}")

print("\n测试完成")
