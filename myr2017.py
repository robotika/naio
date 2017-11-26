# the simplest MYR2017 version

import argparse
import socket
import sys
import struct
import itertools

from logger import LogWriter, LogReader, LogEnd
from robot import Robot

DEFAULT_HOST = '127.0.0.1'    # The remote host
DEFAULT_PORT = 5559              # The same port as used by the server

INPUT_STREAM = 1
OUTPUT_STREAM = 2


class WrapperIO:
    def __init__(self, soc, log, ignore_ref_output=False):
        self.soc = soc
        self.log = log
        self.ignore_ref_output = ignore_ref_output
        self.buf = b''

    def get(self):
        if len(self.buf) < 1024:
            if self.soc is None:
                data = self.log.read(INPUT_STREAM)[2]
            else:
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
        if self.soc is None:
            ref = self.log.read(OUTPUT_STREAM)[2]
            if not self.ignore_ref_output:
                assert naio_msg == ref, (naio_msg, ref)
        else:
            self.log.write(OUTPUT_STREAM, naio_msg)
            self.soc.sendall(naio_msg)


def laser2ascii(scan):
    "Eduro ASCII art"
    step = 5
    scan2 = [x == 0 and 10000 or x for x in scan]
    min_dist_arr = [min(i)/1000.0 for i in 
                        [itertools.islice(scan2, start, start + step) 
                            for start in range(0, len(scan2), step)]]
    s = ''
    for d in min_dist_arr:
        s += (d < 0.5 and 'X' or (d<1.0 and 'x' or (d<1.5 and '.' or ' ')))
    mid = int(len(s)/2)
    s = s[:mid] + 'C' + s[mid:]

    limit = 1.0
    left, right = mid, mid
    while left > 0 and min_dist_arr[left] > limit:
        left -= 1
    while right < len(min_dist_arr) and min_dist_arr[right] > limit:
        right += 1

    return s, mid-left, right-mid


def move_one_meter(robot):
    odo_start = robot.odometry_left_raw + robot.odometry_right_raw
    robot.move_forward()
    dist = 0.0
    while dist < 1.0:
        robot.update()
        odo = robot.odometry_left_raw + robot.odometry_right_raw - odo_start
        dist = 0.06465 * odo / 4.0
    robot.stop()


def turn_right_90deg(robot):
    robot.turn_right()
    for i in range(100):
        robot.update()
    robot.stop()


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
        yield Robot(io.get, io.put)
        print(log.filename)


def main_replay(filename, force):
    "replay existing log file"

    with LogReader(filename) as log:
        print('REPLAY', log.filename)
        io = WrapperIO(None, log, ignore_ref_output=force)
        yield Robot(io.get, io.put)
        print('REPLAY', log.filename)


def play_game(robot, verbose):
        robot.move_forward()
        while True:
            robot.update()
            max_dist = max(robot.laser)
            triplet = laser2ascii(robot.laser)
            s, left, right = triplet
            if left < right:
                robot.move_right()
            elif left > right:
                robot.move_left()
            else:
                robot.move_forward()
            if verbose:
                print('%4d' % max_dist, triplet)
            if max_dist == 0:
                break

        move_one_meter(robot)
        turn_right_90deg(robot)

        robot.stop()
        robot.update()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Navigate Naio robot in "Move Your Robot" competition')
    parser.add_argument('--host', dest='host', default=DEFAULT_HOST,
                        help='IP address of the host')
    parser.add_argument('--port', dest='port', default=DEFAULT_PORT,
                        help='port number of the robot or simulator')
    parser.add_argument('--note', help='add run description')
    parser.add_argument('--verbose', help='show laser output', action='store_true')

    parser.add_argument('--replay', help='replay existing log file')
    parser.add_argument('--force', '-F', dest='force', action='store_true', help='force replay even for failing output asserts')
    args = parser.parse_args()
    
    if args.replay is None:
        for robot in main(args.host, args.port):
            play_game(robot, verbose=args.verbose)
    else:
        for robot in main_replay(args.replay, args.force):
            try:
                play_game(robot, verbose=args.verbose)
            except LogEnd:
                print("Exception LogEnd")

# vim: expandtab sw=4 ts=4
