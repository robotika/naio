# the simplest MYR2017 version

import argparse
import socket
import sys
import struct
import itertools
import zlib
from datetime import timedelta
from threading import Thread

from logger import LogWriter, LogReader, LogEnd
from robot import Robot

DEFAULT_HOST = '127.0.0.1'    # The remote host
DEFAULT_PORT = 5559              # The same port as used by the server

ANNOT_STREAM = 0  # the same as debug/info
INPUT_STREAM = 1
OUTPUT_STREAM = 2
VIDEO_STREAM = 3

VIDEO_COMPRESSION_LEVEL = 7  # zlib parameter


class WrapperIO:
    def __init__(self, soc, log, ignore_ref_output=False):
        self.soc = soc
        self.log = log
        self.ignore_ref_output = ignore_ref_output
        self.buf = b''
        self.time = None

    def get(self):
        if len(self.buf) < 1024:
            if self.soc is None:
                self.time, __, data = self.log.read(INPUT_STREAM)
            else:
                data = self.soc.recv(1024)
                self.time = self.log.write(INPUT_STREAM, data)
            self.buf += data

        assert len(self.buf) > 7 and self.buf[:6] == b'NAIO01', self.buf
        msg_id = self.buf[6]
        size = struct.unpack('>I', self.buf[7:7+4])[0]
        data = self.buf[11:11+size]
        self.buf = self.buf[11+size+4:]  # cut CRC32
        return self.time, msg_id, data

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

    def annot(self, annotation):
        if self.soc is not None:
            self.log.write(ANNOT_STREAM, annotation)


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


def move_straight(robot, how_far):
    robot.annot(b'TAG:move_one_meter:BEGIN')
    odo_start = robot.odometry_left_raw + robot.odometry_right_raw
    robot.move_forward()
    dist = 0.0
    while dist < how_far:
        robot.update()
        odo = robot.odometry_left_raw + robot.odometry_right_raw - odo_start
        dist = 0.06465 * odo / 4.0
    robot.stop()
    robot.annot(b'TAG:move_one_meter:END')


def turn_right_90deg(robot):
    robot.annot(b'TAG:turn_right_90deg:BEGIN')
    robot.turn_right()
    gyro_sum = 0
    start_time = robot.time
    num_updates = 0
    while robot.time - start_time < timedelta(minutes=1):
        prev_time = robot.time
        robot.update()
        dt = robot.time - prev_time
        gyro_sum += robot.gyro_raw[2]  # time is required!
        num_updates += 1
        # the updates are 10Hz (based on laser measurements)
        angle = (gyro_sum * dt.total_seconds()) * 30.5/1000.0
        # also it looks the rotation (in Simulatoz) is clockwise
        if angle > 90.0:  # TODO lower threshold for minor corrections
            break
    robot.stop()
    print('gyro_sum', gyro_sum, robot.time - start_time, num_updates)
    robot.annot(b'TAG:turn_right_90deg:END')


def turn_left_90deg(robot):
    robot.annot(b'TAG:turn_left_90deg:BEGIN')
    robot.turn_left()
    gyro_sum = 0
    start_time = robot.time
    num_updates = 0
    while robot.time - start_time < timedelta(minutes=1):
        prev_time = robot.time
        robot.update()
        dt = robot.time - prev_time
        gyro_sum += robot.gyro_raw[2]  # time is required!
        num_updates += 1
        # the updates are 10Hz (based on laser measurements)
        angle = (gyro_sum * dt.total_seconds()) * 30.5/1000.0
        # also it looks the rotation (in Simulatoz) is clockwise
        if angle < -90.0:  # TODO lower threshold for minor corrections
            break
    robot.stop()
    print('gyro_sum', gyro_sum, robot.time - start_time, num_updates)
    robot.annot(b'TAG:turn_left_90deg:END')


def navigate_row(robot, verbose):
    MAX_GAP_SIZE = 13  # defined for plants on both sides
    OPEN_SIZE = 17
    OFFSET_SIZE = 5
    END_OF_ROW_SIZE = 18 + 19  # for 180deg FOV

    robot.move_forward()
    end_of_row = False

    while not end_of_row:
        robot.update()
        max_dist = max(robot.laser)
        triplet = laser2ascii(robot.laser)
        s, left, right = triplet
        if left + right < MAX_GAP_SIZE:
            if left < right:
                robot.move_right()
            elif left > right:
                robot.move_left()
            else:
                robot.move_forward()
        else:
            # full opening or plans on one side
            if left < MAX_GAP_SIZE and right > OPEN_SIZE:
                # plans on the left
                if left < OFFSET_SIZE:
                    robot.move_right()
                elif left > OFFSET_SIZE:
                    robot.move_left()
                else:
                    robot.move_forward()
            elif left > OPEN_SIZE and right < MAX_GAP_SIZE:
                # unexpected case!
                if OFFSET_SIZE < right:
                    robot.move_right()
                elif OFFSET_SIZE > right:
                    robot.move_left()
                else:
                    robot.move_forward()
            else:
                robot.move_forward()

        if verbose:
            print('%4d' % max_dist, triplet)
        if left + right >= END_OF_ROW_SIZE:
            end_of_row = True


def connect(host, port):
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
        print('could not open socket', (host, port))
        sys.exit(1)
    return s


class VideoRecorder(Thread):

    def __init__(self, soc, log):
        Thread.__init__(self)
        self.setDaemon(True)
        self.soc = soc
        self.log = log

    def run(self):
        print('Video Recorder started')
        while True:
            try:
                data = self.soc.recv(10000)
            except:
                print('Video Terminated')
                break
            # maybe compression could be part of LogWriter??
            self.log.write(VIDEO_STREAM, zlib.compress(data, VIDEO_COMPRESSION_LEVEL))


def main(host, port, video_port=None):
    s = connect(host, port)
    video_socket = None
    if video_port is not None:
        video_socket = connect(host, video_port)

    with s, LogWriter(note=str(sys.argv)) as log:
        print(log.filename)
        io = WrapperIO(s, log)
        
        recorder = None
        if video_socket is not None:
            recorder = VideoRecorder(video_socket, log)
            recorder.start()

        yield Robot(io.get, io.put, io.annot)
        print(log.filename)

        if video_socket is not None:
            video_socket.close()
            recorder.join()


def main_replay(filename, force):
    "replay existing log file"

    with LogReader(filename) as log:
        print('REPLAY', log.filename)
        io = WrapperIO(None, log, ignore_ref_output=force)
        yield Robot(io.get, io.put, io.annot)
        print('REPLAY', log.filename)


def test_1m(robot):
    move_straight(robot, how_far=1.0)
    robot.wait(timedelta(seconds=3))


def test_90deg(robot):
    robot.update()  # define time
    turn_right_90deg(robot)
    robot.wait(timedelta(seconds=3))
    turn_left_90deg(robot)
    robot.wait(timedelta(seconds=3))


def test_loops(robot, verbose):
    for i in range(10):
        navigate_row(robot, verbose)
        move_straight(robot, how_far=1.2)
        turn_right_90deg(robot)
        move_straight(robot, how_far=0.7)
        turn_right_90deg(robot)

    robot.stop()
    robot.update()


def play_game(robot, verbose):

    # 1st row
    navigate_row(robot, verbose)
    move_straight(robot, how_far=1.2)
    turn_right_90deg(robot)
    move_straight(robot, how_far=0.7)
    turn_right_90deg(robot)

    # 2nd row
    navigate_row(robot, verbose)
    move_straight(robot, how_far=1.2)
    turn_left_90deg(robot)
    move_straight(robot, how_far=0.7)
    turn_left_90deg(robot)

    # 3rd row (from outside)
    navigate_row(robot, verbose)
    move_straight(robot, how_far=1.2)
    turn_left_90deg(robot)
    move_straight(robot, how_far=3*0.7)
    turn_left_90deg(robot)

    # 0th row (from outside)
    navigate_row(robot, verbose)
    move_straight(robot, how_far=1.2)

    robot.stop()
    robot.update()


def run_robot(robot, verbose=False, test_case=None):
    if test_case is None:
        play_game(robot, verbose=verbose)
    elif test_case == '1m':
        test_1m(robot)
    elif test_case == '90deg':
        test_90deg(robot)
    elif test_case == 'loops':
        test_loops(robot, verbose=verbose)
    else:
        assert False, test_case  # not supported


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Navigate Naio robot in "Move Your Robot" competition')
    parser.add_argument('--host', dest='host', default=DEFAULT_HOST,
                        help='IP address of the host')
    parser.add_argument('--port', dest='port', default=DEFAULT_PORT,
                        help='port number of the robot or simulator')
    parser.add_argument('--note', help='add run description')
    parser.add_argument('--verbose', help='show laser output', action='store_true')
    parser.add_argument('--video-port', dest='video_port',
                        help='optional video port 5558 for simulator, default "no video"')

    parser.add_argument('--replay', help='replay existing log file')
    parser.add_argument('--force', '-F', dest='force', action='store_true',
                        help='force replay even for failing output asserts')
    parser.add_argument('--test', dest='test_case', help='test cases',
                        choices=['1m', '90deg', 'loops'])
    args = parser.parse_args()
    
    if args.replay is None:
        for robot in main(args.host, args.port, args.video_port):
            run_robot(robot, test_case=args.test_case, verbose=args.verbose)
    else:
        for robot in main_replay(args.replay, args.force):
            try:
                run_robot(robot, test_case=args.test_case, verbose=args.verbose)
            except LogEnd:
                print("Exception LogEnd")

# vim: expandtab sw=4 ts=4
