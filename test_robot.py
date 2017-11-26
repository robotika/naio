import unittest
from queue import Queue
from robot import *


class RoboTest(unittest.TestCase):
    
    def test_odometry(self):
        q_in = Queue()
        q_out = Queue()
        robot = Robot(q_in.get, q_out.put, ODOMETRY_ID)

        q_in.put((ODOMETRY_ID, b'\x00\x00\x00\x00'))
        robot.update()
        self.assertFalse(q_out.empty())
        self.assertEqual(robot.odometry_left_raw, 0)
        self.assertEqual(robot.odometry_right_raw, 0)
        self.assertEqual(q_out.get(), (MOTOR_ID, b'\x00\x00'))

        q_in.put((ODOMETRY_ID, b'\x01\x01\x00\x00'))
        robot.update()
        self.assertFalse(q_out.empty())
        self.assertEqual(robot.odometry_left_raw, 0)
        self.assertEqual(robot.odometry_right_raw, 2)
        self.assertEqual(q_out.get(), (MOTOR_ID, b'\x00\x00'))

# vim: expandtab sw=4 ts=4
