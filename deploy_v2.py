# -*- coding: utf-8 -*-
import paramiko
import time
import socket

def deploy():
    # 创建SSH客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 配置
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    
    try:
        print("正在连接服务器 49.235.105.137 ...")
        
        # 直接连接
        ssh.connect(
            hostname='49.235.105.137',
            port=22,
            username='root',
            password='20040105Jjq',
            timeout=30,
            banner_timeout=30,
            auth_timeout=30,
            sock=sock
        )
        print("连接成功!")
        
        # Git pull
        print("\n执行: git pull origin master")
        stdin, stdout, stderr = ssh.exec_command("cd /root/AIGC_mood && git pull origin master", timeout=30)
        print(stdout.read().decode('utf-8'))
        
        # 安装依赖
        print("\n安装依赖...")
        stdin, stdout, stderr = ssh.exec_command("pip install PyPDF2 python-docx -q", timeout=60)
        print(stdout.read().decode('utf-8'))
        
        # 重启服务
        print("\n重启服务...")
        ssh.exec_command("neo4j start")
        time.sleep(5)
        
        ssh.exec_command("pkill -f admin_server; cd /root/AIGC_mood && nohup python3 admin_server.py > /tmp/admin.log 2>&1 &")
        time.sleep(2)
        
        ssh.exec_command("pkill -f my_rag_knowledge_api; cd /root/AIGC_mood && nohup python3 my_rag_knowledge_api.py > /tmp/rag.log 2>&1 &")
        time.sleep(2)
        
        ssh.exec_command("pkill -f document_knowledge_api; cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc.log 2>&1 &")
        time.sleep(3)
        
        # 检查状态
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp | grep -E ':(5001|5002|5005)'", timeout=10)
        print("\n服务端口状态:")
        print(stdout.read().decode('utf-8'))
        
        print("\n部署完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
