import unittest
from queue import Queue
from datetime import timedelta

from robot import *


class RoboTest(unittest.TestCase):
    
    def test_odometry(self):
        q_in = Queue()
        q_out = Queue()
        robot = Robot(q_in.get, q_out.put, term=ODOMETRY_ID)

        dt = timedelta(microseconds = 200)
        q_in.put((dt, ODOMETRY_ID, b'\x00\x00\x00\x00'))
        robot.update()
        self.assertEqual(robot.time, dt)
        self.assertFalse(q_out.empty())
        self.assertEqual(robot.odometry_left_raw, 0)
        self.assertEqual(robot.odometry_right_raw, 0)
        self.assertEqual(q_out.get(), (MOTOR_ID, b'\x00\x00'))

        q_in.put((2*dt, ODOMETRY_ID, b'\x01\x01\x00\x00'))
        robot.update()
        self.assertFalse(q_out.empty())
        self.assertEqual(robot.odometry_left_raw, 0)
        self.assertEqual(robot.odometry_right_raw, 2)
        self.assertEqual(q_out.get(), (MOTOR_ID, b'\x00\x00'))

    def test_annotations(self):
        q_in = Queue()
        q_out = Queue()
        q_annot = Queue()
        robot = Robot(q_in.get, q_out.put, annot=q_annot.put)

        robot.annot(b'TAG:turn_right_90deg:BEGIN')
        self.assertEqual(q_annot.get_nowait(), b'TAG:turn_right_90deg:BEGIN')

    def test_wait(self):
        q_in = Queue()
        q_out = Queue()
        robot = Robot(q_in.get, q_out.put, term=ODOMETRY_ID)

        dt = timedelta(seconds = 1)
        for i in range(10):
            q_in.put((i * dt, ODOMETRY_ID, b'\x00\x00\x00\x00'))

        robot.wait(timedelta(seconds=3))
        self.assertEqual(q_out.qsize(), 3 + 1)  # extra update for undefined time

        robot.wait(timedelta(seconds=3))
        self.assertEqual(q_out.qsize(), 3 + 1 + 3)

# vim: expandtab sw=4 ts=4
