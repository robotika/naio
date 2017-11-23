"""
Parse already logged data.
usage:
   python logparser.py <log file>
"""

import sys
import struct


def parse(filename):
    with open(filename, 'rb') as f:
        prev_odo = b'\x00\x00\x00\x00'
        dist = 0
        while True:
            prefix = f.read(6)
            if len(prefix) == 0:
                break
            assert prefix == b'NAIO01', prefix
            msg_id = f.read(1)
            size = struct.unpack('>I', f.read(4))[0]
            data = f.read(size)
            if msg_id == b'\x06':
                diff = sum([a^b for a, b in zip(prev_odo, data)])
                prev_odo = data
                dist += diff
            crc32 = struct.unpack('I', f.read(4))[0]
        print('Total distance %.2fm' % (dist * 6.465/400.0))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(-1)
    parse(sys.argv[1])

# vim: expandtab sw=4 ts=4
