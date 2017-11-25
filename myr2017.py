# simplest version

import argparse
import socket
import sys
import struct
import datetime


DEFAULT_HOST = '127.0.0.1'    # The remote host
DEFAULT_PORT = 5559              # The same port as used by the server

def main(host, port):
    s = None
    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
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
        print(filename)
        f = open(filename, 'wb')
        prev_time = datetime.datetime.now()
        while True:
            data = s.recv(1024)
            f.write(data)
            f.flush()
            assert len(data) > 7 and data[:6] == b'NAIO01', data

            msg_id = data[6]
            size = struct.unpack('>I', data[7:7+4])[0]

            # odometry
            if msg_id == 0x06:
                t = datetime.datetime.now()
                s.sendall(b'NAIO01\x01\x00\x00\x00\x02\x70\x70\xCD\xCD\xCD\xCD')
                prev_time = t
            elif msg_id == 0x07:
                assert size == 2*271 + 271, size
                scan = struct.unpack('>' + 'H'*271, data[11:11+2*271])
                print(max(scan))
                if max(scan) == 0:
                    break
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Navigate Naio robot in "Move Your Robot" competition')
    parser.add_argument('--host', dest='host', default=DEFAULT_HOST,
                        help='IP address of the host')
    parser.add_argument('--port', dest='port', default=DEFAULT_PORT,
                        help='port number of the robot or simulator')
    args = parser.parse_args()
    
    main(args.host, args.port)

# vim: expandtab sw=4 ts=4
