import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# 测试健康检查
print("测试健康检查...")
r = requests.get('http://49.235.105.137:5002/health')
print(f"状态: {r.status_code}, 响应: {r.json()}")

# 测试文本处理
print("\n测试文本处理...")
text = """
心理咨询是一种帮助人们解决心理问题、维护心理健康的专业服务。
心理咨询师通过与来访者的对话，帮助他们了解自己的情绪和行为。

焦虑症是一种常见的心理障碍，表现为持续的担忧、紧张和恐惧。
焦虑症的症状包括心慌、出汗、颤抖等。
治疗方法包括药物治疗、心理治疗和生活方式调整。
"""

data = {"text": text, "name": "心理健康知识", "category": "心理学"}
r = requests.post('http://49.235.105.137:5002/api/document/process-text', json=data)
print(f"状态: {r.status_code}")
if r.status_code == 200:
    result = r.json()
    if result.get('success'):
        d = result.get('data', {})
        print(f"文档: {d.get('doc_name')}, 字符数: {d.get('total_chars')}, 块数: {d.get('total_chunks')}")
        print(f"关键词: {d.get('keywords')}")
        print(f"摘要: {d.get('summary', '')[:80]}...")
    else:
        print(f"错误: {result.get('error')}")
