# simplest version

# Echo client program
import socket
import sys

HOST = '127.0.0.1'    # The remote host
PORT = 5559              # The same port as used by the server
s = None
for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        s = socket.socket(af, socktype, proto)
    except OSError as msg:
        s = None
        continue
    try:
        s.connect(sa)
    except OSError as msg:
        s.close()
        s = None
        continue
    break
if s is None:
    print('could not open socket')
    sys.exit(1)
with s:
#    s.sendall(b'Hello, world')
    f = open('data171122.bin', 'wb')
    for i in range(1000):
        data = s.recv(1024)
        print(data)
        f.write(data)
        f.flush()
    f.close()

