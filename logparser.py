"""
Parse already logged data.
usage:
   python logparser.py <log file>
"""

import sys
import struct


def parse(filename):
    with open(filename, 'rb') as f:
        while True:
            prefix = f.read(6)
            if len(prefix) == 0:
                break
            assert prefix == b'NAIO01', prefix
            msg_id = f.read(1)
            size = struct.unpack('>I', f.read(4))[0]
            data = f.read(size)
            if msg_id == b'\x06':
                print(data)
            crc32 = struct.unpack('I', f.read(4))[0]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(-1)
    parse(sys.argv[1])