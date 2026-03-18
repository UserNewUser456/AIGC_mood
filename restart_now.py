# -*- coding: utf-8 -*-
import paramiko
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_ssh_command(host, port, username, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"正在连接 {host}...")
        client.connect(host, port=port, username=username, password=password, timeout=30)
        print("连接成功!")
        
        # 检查Neo4j状态
        stdin, stdout, stderr = client.exec_command("neo4j status")
        status = stdout.read().decode('utf-8').strip()
        print(f"Neo4j状态: {status}")
        
        if "not running" in status.lower() or not status:
            print("启动Neo4j...")
            client.exec_command("neo4j start")
            time.sleep(8)
        
        # 启动服务
        print("启动管理员服务...")
        client.exec_command("cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &")
        time.sleep(2)
        
        print("启动RAG服务...")
        client.exec_command("cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
        time.sleep(2)
        
        print("启动文档知识服务...")
        client.exec_command("cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &")
        time.sleep(3)
        
        # 检查服务
        stdin, stdout, stderr = client.exec_command("ps aux | grep -E 'python3.*(admin_server|my_rag|document_knowledge)' | grep -v grep")
        services = stdout.read().decode('utf-8').strip()
        print(f"运行中的服务:\n{services}")
        
        client.close()
        print("\n✅ 所有服务已启动!")
        return True
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

if __name__ == "__main__":
    run_ssh_command("49.235.105.137", 22, "root", "20040105Jjq", "")
