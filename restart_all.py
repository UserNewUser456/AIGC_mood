import paramiko, time
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=30)

# 启动Neo4j
print("启动Neo4j...")
client.exec_command("neo4j start")
time.sleep(8)

# 重启所有服务
print("重启服务...")
client.exec_command("pkill -f admin_server; pkill -f my_rag; pkill -f document_knowledge")
time.sleep(2)
client.exec_command("cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &")
time.sleep(2)
client.exec_command("cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
time.sleep(2)
client.exec_command("cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &")
time.sleep(3)

# 检查状态
stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep -E '5001|5002|5005'")
print("\n端口状态:")
print(stdout.read().decode())

print("\n完成!")
client.close()
