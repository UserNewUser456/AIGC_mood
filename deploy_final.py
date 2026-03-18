import paramiko
import time

print("连接服务器...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(
        hostname='49.235.105.137',
        port=22,
        username='root',
        password='20040105Jjq',
        timeout=60,
        allow_agent=False,
        look_for_keys=False
    )
    print("连接成功!")

    # 安装依赖
    print("安装依赖...")
    stdin, stdout, stderr = client.exec_command("pip install PyPDF2 python-docx -q", timeout=120)
    print(stdout.read().decode('utf-8'))

    # 启动Neo4j
    print("启动Neo4j...")
    stdin, stdout, stderr = client.exec_command("neo4j start")
    print(stdout.read().decode('utf-8'))
    time.sleep(5)

    # 重启管理员后台
    print("启动管理员后台 (5005)...")
    client.exec_command("pkill -f admin_server || true")
    time.sleep(1)
    client.exec_command("cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &")
    time.sleep(2)

    # 重启RAG服务
    print("启动RAG知识图谱服务 (5001)...")
    client.exec_command("pkill -f my_rag_knowledge_api || true")
    time.sleep(1)
    client.exec_command("cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
    time.sleep(2)

    # 启动文档知识API
    print("启动文档知识API (5002)...")
    client.exec_command("pkill -f document_knowledge_api || true")
    time.sleep(1)
    client.exec_command("cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &")
    time.sleep(3)

    # 检查状态
    print("\n检查服务端口...")
    stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep -E ':(5001|5002|5005)'")
    print(stdout.read().decode('utf-8'))

    print("\n部署完成!")
    print("服务地址:")
    print("  - 管理员后台: http://49.235.105.137:5005")
    print("  - RAG知识图谱: http://49.235.105.137:5001")
    print("  - 文档知识API: http://49.235.105.137:5002")

    client.close()

except Exception as e:
    print(f"错误: {e}")
