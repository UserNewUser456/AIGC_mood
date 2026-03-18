import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=30)

# 检查端口
stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep -E ':(5001|5002|5005)'")
print("端口状态:")
print(stdout.read().decode('utf-8'))

# 检查文档API日志
print("\n文档API日志:")
stdin, stdout, stderr = client.exec_command("tail -30 /tmp/doc.log")
log = stdout.read().decode('utf-8')
print(log)

if "error" in log.lower() or "traceback" in log.lower():
    print("\n发现错误!")
else:
    print("\n服务正常运行")

client.close()
