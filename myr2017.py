# simplest version

# Echo client program
import socket
import sys
import datetime


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
    # commad to drive motors
    s.sendall(b'NAIO01\x01\x00\x00\x00\x02\x70\x70\xCD\xCD\xCD\xCD')
    filename = datetime.datetime.now().strftime("naio%y%m%d_%H%M%S.log")
    f = open(filename, 'wb')
    prev_time = datetime.datetime.now()
    for i in range(1000):
        data = s.recv(1024)
        assert len(data) > 7 and data[:6] == b'NAIO01', data

        # odometry
        if data[6] == 0x06:
            t = datetime.datetime.now()
            print((t - prev_time).microseconds, data)
            prev_time = t
            # alive command
            s.sendall(b'NAIO01\xB4\x00\x00\x00\x01' + bytes([i%256,]) + b'\xCD\xCD\xCD\xCD')
            s.sendall(b'NAIO01\x01\x00\x00\x00\x02\x70\x70\xCD\xCD\xCD\xCD')
        f.write(data)
        f.flush()
    f.close()

# vim: expandtab sw=4 ts=4
