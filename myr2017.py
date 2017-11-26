# the simplest MYR2017 version

import argparse
import socket
import sys
import struct

from logger import LogWriter
from robot import Robot

DEFAULT_HOST = '127.0.0.1'    # The remote host
DEFAULT_PORT = 5559              # The same port as used by the server

INPUT_STREAM = 1
OUTPUT_STREAM = 2


class WrapperIO:
    def __init__(self, soc, log):
        self.soc = soc
        self.log = log
        self.buf = b''

    def get(self):
        if len(self.buf) < 1024:
            data = self.soc.recv(1024)
            self.log.write(INPUT_STREAM, data)
            self.buf += data

        assert len(self.buf) > 7 and self.buf[:6] == b'NAIO01', self.buf
        msg_id = self.buf[6]
        size = struct.unpack('>I', self.buf[7:7+4])[0]
        data = self.buf[11:11+size]
        self.buf = self.buf[11+size+4:]  # cut CRC32
        return msg_id, data

    def put(self, cmd):
        msg_id, data = cmd
        naio_msg = b'NAIO01' + bytes([msg_id]) + struct.pack('>I', len(cmd)) + data + b'\xCD\xCD\xCD\xCD'
        self.log.write(OUTPUT_STREAM, naio_msg)
        self.soc.sendall(naio_msg)


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

    with s, LogWriter(note=str(sys.argv)) as log:
        print(log.filename)

        io = WrapperIO(s, log)
        
        robot = Robot(io.get, io.put)
        robot.set_speed(0.5, 0.0)
        while True:
            robot.update()
            max_dist = max(robot.laser)
            print(max_dist)
            if max_dist == 0:
                break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Navigate Naio robot in "Move Your Robot" competition')
    parser.add_argument('--host', dest='host', default=DEFAULT_HOST,
                        help='IP address of the host')
    parser.add_argument('--port', dest='port', default=DEFAULT_PORT,
                        help='port number of the robot or simulator')
    parser.add_argument('--note', help='add run description')    
    args = parser.parse_args()
    
    main(args.host, args.port)

# vim: expandtab sw=4 ts=4
