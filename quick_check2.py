import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=30)

# 检查端口
stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep -E '5001|5002|5005'")
print("端口状态:", stdout.read().decode())

# 检查进程
stdin, stdout, stderr = client.exec_command("ps aux | grep python | grep -E 'admin_server|my_rag|document_knowledge'")
print("进程状态:", stdout.read().decode())

# 检查Neo4j
stdin, stdout, stderr = client.exec_command("neo4j status")
print("Neo4j:", stdout.read().decode())

client.close()
