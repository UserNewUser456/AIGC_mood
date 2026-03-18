# -*- coding: utf-8 -*-
import paramiko
import time
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_neo4j():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("连接服务器...")
        ssh.connect(hostname='49.235.105.137', port=22, username='root', password='20040105Jjq', timeout=10)
        print("连接成功!")
        
        # 停止Neo4j
        print("\n停止Neo4j...")
        ssh.exec_command("neo4j stop")
        time.sleep(3)
        
        # 修改neo4j配置，禁用认证
        print("修改neo4j配置，禁用认证...")
        ssh.exec_command("sed -i 's/# dbms.security.auth_enabled=true/dbms.security.auth_enabled=false/' /etc/neo4j/neo4j.conf")
        ssh.exec_command("echo 'dbms.security.auth_enabled=false' >> /etc/neo4j/neo4j.conf")
        
        # 启动Neo4j
        print("启动Neo4j...")
        ssh.exec_command("neo4j start")
        time.sleep(8)
        
        # 检查状态
        stdin, stdout, stderr = ssh.exec_command("neo4j status")
        print("Neo4j状态:", stdout.read().decode('utf-8'))
        
        # 重启RAG服务
        print("\n重启RAG服务...")
        ssh.exec_command("pkill -f my_rag_knowledge_api")
        time.sleep(2)
        ssh.exec_command("cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
        time.sleep(3)
        
        # 检查端口
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp | grep -E ':(5001|5005)'")
        print("\n服务状态:")
        print(stdout.read().decode('utf-8'))
        
        print("\n修复完成!")
        ssh.close()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    fix_neo4j()
