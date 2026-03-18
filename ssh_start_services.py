# -*- coding: utf-8 -*-
"""
使用Python和paramiko库连接SSH服务器
需要先安装paramiko: pip install paramiko
"""
import paramiko
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def connect_and_start():
    # 创建SSH客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 连接服务器
        print("正在连接服务器...")
        ssh.connect(
            hostname='49.235.105.137',
            port=22,
            username='root',
            password='20040105Jjq',
            timeout=10
        )
        print("连接成功!")
        
        # 启动Neo4j
        print("\n启动Neo4j...")
        stdin, stdout, stderr = ssh.exec_command("neo4j start")
        print(stdout.read().decode('utf-8'))
        time.sleep(5)
        
        # 检查Neo4j状态
        stdin, stdout, stderr = ssh.exec_command("neo4j status")
        print("Neo4j状态:", stdout.read().decode('utf-8'))
        
        # 启动管理员后台服务
        print("\n启动管理员后台服务 (端口5005)...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &")
        time.sleep(2)
        
        # 启动RAG知识图谱服务
        print("启动RAG知识图谱服务 (端口5001)...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
        time.sleep(3)
        
        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp | grep -E ':(5001|5005)'")
        print("\n服务端口状态:")
        print(stdout.read().decode('utf-8'))
        
        print("\n✅ 所有服务启动完成!")
        
        ssh.close()
        
    except paramiko.AuthenticationException:
        print("❌ 认证失败，请检查密码")
    except paramiko.SSHException as e:
        print(f"❌ SSH连接错误: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    connect_and_start()
