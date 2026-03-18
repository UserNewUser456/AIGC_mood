import requests, json
# 测试
print("测试健康检查...")
r = requests.get('http://49.235.105.137:5002/health', timeout=10)
print(f"状态: {r.status_code}")
print(f"响应: {r.json()}")

print("\n测试文本处理...")
data = {"text": "心理咨询是帮助人们解决心理问题的专业服务。焦虑症表现为持续的紧张和担忧。", "name": "心理知识"}
r = requests.post('http://49.235.105.137:5002/api/document/process-text', json=data, timeout=15)
print(f"状态: {r.status_code}")
print(f"响应: {json.dumps(r.json(), indent=2, ensure_ascii=False)[:500]}")
