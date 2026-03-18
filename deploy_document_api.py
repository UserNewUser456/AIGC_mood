# -*- coding: utf-8 -*-
import paramiko
import time
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def deploy_document_api():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("连接服务器...")
        ssh.connect(hostname='49.235.105.137', port=22, username='root', password='20040105Jjq', timeout=10)
        print("连接成功!")
        
        # 上传文件
        print("\n上传文档处理模块...")
        
        files_to_upload = [
            ('document_processor.py', 'document_processor.py'),
            ('document_knowledge_api.py', 'document_knowledge_api.py')
        ]
        
        for local_file, remote_file in files_to_upload:
            print(f"上传 {local_file}...")
            sftp = ssh.open_sftp()
            sftp.put(local_file, f'/root/AIGC_mood/{remote_file}')
            sftp.close()
        
        # 安装依赖
        print("\n安装Python依赖...")
        ssh.exec_command("pip install PyPDF2 python-docx langchain langchain-community -q")
        time.sleep(2)
        
        # 启动文档知识API服务
        print("\n启动文档知识API服务 (端口5002)...")
        ssh.exec_command("pkill -f document_knowledge_api || true")
        time.sleep(1)
        ssh.exec_command("cd /root/AIGC_mood && nohup python3 document_knowledge_api.py > /tmp/doc_api.log 2>&1 &")
        time.sleep(3)
        
        # 检查端口
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp | grep 5002")
        print("\n端口状态:")
        print(stdout.read().decode('utf-8'))
        
        print("\n部署完成!")
        ssh.close()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    deploy_document_api()
