"""
Parse already logged data.
usage:
   python logparser.py <log file>
"""

import math
import sys
import struct
import itertools

import matplotlib.pyplot as plt


def parse(filename):
    with open(filename, 'rb') as f:
        prev_odo = b'\x00\x00\x00\x00'
        total_dist_raw = 0
        arr = []
        pose_arr = []
        while True:
            prefix = f.read(6)
            if len(prefix) == 0:
                break
            assert prefix == b'NAIO01', prefix
            msg_id = f.read(1)
            size = struct.unpack('>I', f.read(4))[0]
            data = f.read(size)
            crc32 = struct.unpack('I', f.read(4))[0]

            # Odometry
            if msg_id == b'\x06':
                diff = sum([a^b for a, b in zip(prev_odo, data)])
                prev_odo = data
                total_dist_raw += diff
            
            # Laser
            if msg_id == b'\x07':
                assert size == 2*271 + 271, size
                scan = struct.unpack('>' + 'H'*271, data[:2*271])
                
                d = total_dist_raw * 6.465/400.0
                pose_arr.append((d, 0))
                for i, dist_mm in enumerate(scan):
                    if dist_mm > 0:
                        angle = math.radians(i-135.0)
                        dist = dist_mm/1000.0
                        x, y = d + math.cos(angle)*dist, math.sin(angle)*dist
                        arr.append((x, y))

                # Eduro ASCII art
                step = 5
                scan2 = [x == 0 and 10000 or x for x in scan]
                min_dist_arr = [min(i)/1000.0 for i in 
                        [itertools.islice(scan2, start, start + step) 
                            for start in range(0, len(scan2), step)]]
                s = ''
                for i in min_dist_arr:
                    s += (i < 0.5 and 'X' or (i<1.0 and 'x' or (i<1.5 and '.' or ' ')))
                print(s)

        plt.plot([x for x, _ in arr], [y for _, y in arr],
                             'o', linewidth=2)
        plt.plot([x for x, _ in pose_arr], [y for _, y in pose_arr],
                             'go', linewidth=2)
        plt.axes().set_aspect('equal', 'datalim')
        plt.show()
                    

        print('Total distance %.2fm' % (total_dist_raw * 6.465/400.0))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(-1)
    parse(sys.argv[1])

# vim: expandtab sw=4 ts=4
