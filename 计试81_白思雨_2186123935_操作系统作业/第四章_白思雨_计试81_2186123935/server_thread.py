import socket
from threading import Thread
 
 
s = socket.socket()
host = socket.gethostname()
s.bind((host,1234))
s.listen(100)
print("Waiting for connection......")
 
def tcplink(sock,addr):
    print("Accept new connection from %s:%s" % addr)
    data = sock.recv(1024)
    i = int(data)
    sock.send(bytes(str(i*i*i*i), encoding = 'utf8'))
    sock.close()
    print("connection closed!")
 
while True:
    sock, addr = s.accept()
    t = Thread(target = tcplink, args = (sock,addr))
    t.start()
