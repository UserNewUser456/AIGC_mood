import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=30)

# 安装依赖
print("安装依赖...")
stdin, stdout, stderr = client.exec_command("pip install PyPDF2 python-docx langchain langchain-community -q", timeout=120)
print(stdout.read().decode())
print(stderr.read().decode())

# 重启文档API
print("\n重启文档API...")
client.exec_command("pkill -f document_knowledge_api")
import time
time.sleep(2)
client.exec_command("cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &")
time.sleep(3)

# 检查日志
stdin, stdout, stderr = client.exec_command("tail -20 /tmp/doc.log")
print("\n文档API日志:")
print(stdout.read().decode())

client.close()
