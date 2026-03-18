import paramiko
import time

print("尝试连接...")
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
    
    stdin, stdout, stderr = client.exec_command("git -C /root/AIGC_mood pull origin master", timeout=60)
    print("Git pull结果:")
    print(stdout.read().decode('utf-8'))
    
    client.close()
    print("完成!")
    
except Exception as e:
    print(f"失败: {type(e).__name__}: {e}")
