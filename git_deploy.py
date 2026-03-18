# -*- coding: utf-8 -*-
import paramiko
import time
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def git_pull_and_deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("连接服务器...")
        ssh.connect(hostname='49.235.105.137', port=22, username='root', password='20040105Jjq', timeout=10)
        print("连接成功!")

        # 1. 拉取最新代码
        print("\n从Git拉取最新代码...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/AIGC_mood && git pull origin master")
        print(stdout.read().decode('utf-8'))
        if stderr.read():
            pass

        # 2. 安装依赖
        print("\n安装Python依赖...")
        ssh.exec_command("pip install PyPDF2 python-docx langchain langchain-community -q")
        time.sleep(3)

        # 3. 重启所有服务
        print("\n重启所有服务...")

        # Neo4j
        ssh.exec_command("neo4j start")
        time.sleep(5)

        # 管理员后台 (5005)
        print("启动管理员后台 (5005)...")
        ssh.exec_command("pkill -f admin_server || true")
        time.sleep(1)
        ssh.exec_command("cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &")
        time.sleep(2)

        # RAG知识图谱服务 (5001)
        print("启动RAG服务 (5001)...")
        ssh.exec_command("pkill -f my_rag_knowledge_api || true")
        time.sleep(1)
        ssh.exec_command("cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
        time.sleep(2)

        # 文档知识API服务 (5002)
        print("启动文档知识API (5002)...")
        ssh.exec_command("pkill -f document_knowledge_api || true")
        time.sleep(1)
        ssh.exec_command("cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &")
        time.sleep(3)

        # 4. 检查服务状态
        print("\n检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp | grep -E ':(5001|5002|5005)'")
        print("端口监听状态:")
        print(stdout.read().decode('utf-8'))

        # 5. 检查Neo4j
        stdin, stdout, stderr = ssh.exec_command("neo4j status")
        print("\nNeo4j状态:")
        print(stdout.read().decode('utf-8'))

        print("\n✅ 部署完成!")
        print("服务地址:")
        print("  - 管理员后台: http://49.235.105.137:5005")
        print("  - RAG知识图谱: http://49.235.105.137:5001")
        print("  - 文档知识API: http://49.235.105.137:5002")

        ssh.close()

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    git_pull_and_deploy()
