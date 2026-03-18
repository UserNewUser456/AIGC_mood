import paramiko, sys
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=30)
    stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep -E ':(5001|5002|5005)'")
    print(stdout.read().decode('utf-8'))
    client.close()
except Exception as e:
    print(f"Error: {e}")
