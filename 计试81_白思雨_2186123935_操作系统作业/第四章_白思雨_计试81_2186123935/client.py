import socket
import time
 
 
time1 = time.time()
for i in range(1,100):
    s = socket.socket()
    host = socket.gethostname()
    port = 1234
    s.connect((host,port))
    s.send(bytes('20', encoding = 'utf8'))
    print(s.recv(1024).decode('utf-8'))
 
time2 = time.time()
print(time2 - time1)
