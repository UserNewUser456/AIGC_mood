import requests, json
r = requests.post('http://49.235.105.137:5002/api/document/process-text', 
    json={"text": "心理咨询是帮助人们解决心理问题的专业服务。焦虑症表现为持续的紧张、担忧和恐惧。治疗方法包括认知行为疗法和药物治疗。", "name": "心理知识", "category": "心理学"})
print(r.status_code)
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
