"""
Parse already logged data.
usage:
   python logparser.py <log file>
"""

import argparse
import math
import sys
import struct
import itertools
from datetime import timedelta

import matplotlib.pyplot as plt

from logger import LogReader, LogEnd


INPUT_STREAM = 1

def naio_packets(log):
    WRAP_SIZE = 6 + 1 + 4 + 4  # NAIO01, type, size + CRC32
    buf = b''
    delta = timedelta()
    read_more = True
    while True:
        if read_more:
            try:
                delta, __, data = log.read(INPUT_STREAM)
                buf += data
                read_more = False
            except LogEnd:
                break

        if len(buf) >= WRAP_SIZE:
            prefix = buf[:6]
            assert prefix == b'NAIO01', prefix
            if prefix == b'NAIO01':
                size = struct.unpack_from('>I', buf, 6+1)[0]
                if len(buf) >= size + WRAP_SIZE:
                    yield delta, buf[:size + WRAP_SIZE]
                    buf = buf[size + WRAP_SIZE:]
                else:
                    read_more = True
            else:
                print('Skipping', buf[0])
                buf = buf[1:]  # cut one byte
        else:
            read_more = True


def parse(filename, verbose, gyro_output=False):
    with LogReader(filename) as log:
        prev_odo = b'\x00\x00\x00\x00'
        total_dist_raw = 0
        arr = []
        pose_arr = []
        gyro_arr = []
        for delta, item in naio_packets(log):
            prefix, item = item[:6], item[6:]
            assert prefix == b'NAIO01', prefix
            msg_id, item = item[:1], item[1:]
            size, item = struct.unpack('>I', item[:4])[0], item[4:]
            data, item = item[:size], item[size:]
            crc32, item = struct.unpack('I', item[:4])[0], item[4:]
            assert item == b'', item  # failing now due to multiple message in the buffer

            # Odometry
            if msg_id == b'\x06':
                diff = sum([a^b for a, b in zip(prev_odo, data)])
                prev_odo = data
                total_dist_raw += diff

            # Gyro
            if msg_id == b'\x0A':
                assert len(data) == 6, len(data)
                # X, Y, Z (gain factor 30.5)
                gyro_raw = struct.unpack('>hhh', data)
                #print(gyro_raw[2])
                gyro_arr.append((delta.total_seconds() , [x * 30.5 / 1000.0 for x in gyro_raw]))

            # Laser
            if msg_id == b'\x07':
                assert size == 2*271 + 271, size
                scan = struct.unpack('>' + 'H'*271, data[:2*271])
                
                # restrict laser view to 180deg
                scan = scan[45:-45]

                d = total_dist_raw * 6.465/400.0
                pose_arr.append((d, 0))
                for i, dist_mm in enumerate(scan):
                    if dist_mm > 0:
                        angle = math.radians(i-90.0)
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
                if verbose:
                    print(s)

        if gyro_output:
            plt.plot([x for x, _ in gyro_arr], [y for _, y in gyro_arr], 'o-')
            plt.xlabel('time (sec)')
            plt.ylabel('angular velocity (deg/sec)')
        else:
            plt.plot([x for x, _ in arr], [y for _, y in arr],
                                 'o', linewidth=2)
            plt.plot([x for x, _ in pose_arr], [y for _, y in pose_arr],
                                 'go', linewidth=2)
            plt.axes().set_aspect('equal', 'datalim')
        plt.show()
                    

        print('Total distance %.2fm' % (total_dist_raw * 6.465/400.0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse already logged data.')
    parser.add_argument('filename', help='logfile')
    parser.add_argument('--verbose', '-v', action='store_true', help='print intermediate output')
    parser.add_argument('--gyro', action='store_true', help='show gyro data')
    args = parser.parse_args()

    parse(args.filename, verbose=args.verbose, gyro_output=args.gyro)

# vim: expandtab sw=4 ts=4
