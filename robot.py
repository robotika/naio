# a robot with put/get items interface

import struct


MOTOR_ID = 0x01
ODOMETRY_ID = 0x05
LASER_ID = 0x07


class Robot:
    def __init__(self, get, put, term=LASER_ID):
        "provide input and output methods"
        self.get = get
        self.put = put
        self.term = term
        
        self.laser = None
        self.odometry_left_raw = 0
        self.odometry_right_raw = 0

        self.motor_pwm = [0, 0]
        self.prev_odo = None

    def update(self):
        while True:
            msg_type, data = self.get()
            if msg_type == LASER_ID:
                self.update_laser(data)
            elif msg_type == ODOMETRY_ID:
                self.update_odometry(data)

            if msg_type == self.term:
                break

        self.put((MOTOR_ID, self.get_motor_cmd()))

    def set_speed(self, speed, angular_speed):
        assert angular_speed == 0.0  # not implemented yet
        if speed > 0.0:
            self.motor_pwm = [0x70, 0x70]
        elif speed < 0.0:
            self.motor_pwm = [-0x70, -0x70]
        else:
            self.motor_pwm = [0, 0]

    def update_laser(self, data):
        assert len(data) == 2*271 + 271, len(data)
        self.laser = struct.unpack('>' + 'H'*271, data[:2*271])

    def update_odometry(self, data):
        assert len(data) == 4, len(data)
        # FR, RR, RL, FL
        if self.prev_odo is not None:
            diff = [a^b for a, b in zip(self.prev_odo, data)]
            self.odometry_right_raw += diff[0] + diff[1]
            self.odometry_left_raw += diff[2] + diff[3]
        self.prev_odo = data


    def get_motor_cmd(self):
        return bytes(self.motor_pwm)

# vim: expandtab sw=4 ts=4
