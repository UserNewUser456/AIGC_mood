# Test SSH connection
import paramiko
import sys

try:
    print("Connecting...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=30)
    print("SSH连接成功!")
    stdin, stdout, stderr = client.exec_command("neo4j status")
    print("Neo4j:", stdout.read().decode().strip())
    client.close()
except Exception as e:
    print(f"Error: {e}")
