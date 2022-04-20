from enum import Enum

import serial


class Motor(Enum):
    Pitch = 0   # Up and down
    Yaw = 1     # Left and right

class MotorController:
    r = None
    source = None
    baud_rate = None

    def __init__(self, source: str, baud_rate=115200):
        # Connect to microcontroller
        self.source = source
        self.baud_rate = baud_rate

        self.r = serial.Serial(self.source, self.baud_rate, timeout=1, write_timeout=1)

    def move_to_position(self, motor: Motor, angle: int):
        """
        Moves motor to a specified position
        Angle is in increments of tenths of degrees
        For example, to move to 45 degrees, send 450
        0 is center
        """

        self.r.write(f"{motor} {angle}\n")
