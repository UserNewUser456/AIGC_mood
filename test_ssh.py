import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('49.235.105.137', 22, 'root', '20040105Jjq', timeout=20)
print('SSH连接成功!')
stdin, stdout, stderr = c.exec_command("echo test")
print(stdout.read().decode())
c.close()
