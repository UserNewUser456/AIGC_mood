# Test Document API text processing
import requests
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=== 测试文档知识提取API ===\n")

# 测试文本处理
text = """
心理咨询是帮助人们解决心理问题的专业服务。焦虑症是一种常见的心理健康问题，
表现为持续的紧张、担忧和恐惧。治疗方法包括认知行为疗法、药物治疗和心理疏导。
正念冥想是一种有效的放松技巧，可以帮助缓解焦虑情绪。
运动疗法也是推荐的辅助治疗方法，定期运动可以改善情绪状态。
"""

data = {
    "text": text,
    "name": "心理健康知识",
    "category": "心理学"
}

print("发送请求...")
try:
    r = requests.post(
        "http://49.235.105.137:5002/api/document/process-text",
        json=data,
        timeout=30
    )
    result = r.json()
    print(f"状态: {r.status_code}")
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"错误: {e}")
