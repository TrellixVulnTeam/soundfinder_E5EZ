import time

import serial

from threading import Thread


class MotorController:
    r = None
    source = None
    baud_rate = None
    t1 = None

    def __init__(self, source: str, baud_rate=115200):
        # Connect to microcontroller
        self.source = source
        self.baud_rate = baud_rate

        self.r = serial.Serial(self.source, self.baud_rate)
        time.sleep(1)

        self.t1 = Thread(target=self.listen)
        self.t1.start()

    def move(self, angle: int):
        """
        Moves motor to a specified position
        Angle in increments of a tenth of a degree and can be between -900 and 900
        :param angle:   The angle to move to in tenths of degree. So to move to 45, send 450
        """

        if angle < -900 or angle > 900:
            raise ValueError("Angle cannot be below -900 or above 900")

        if angle < 0:
            # out = f'B{abs(angle)}'.encode('utf-8')
            self.r.write(b'B')
            self.r.write(abs(angle))
            self.r.write(b'\n')
        else:
            # out = f'{angle}'.encode('utf-8')
            # self.r.writelines(out)
            self.r.write(b'A')
            self.r.write(angle)
            self.r.write(b'\n')

    def test(self):
        self.r.write(b"Poggers")

    def listen(self):
        while True:
            data = self.r.read(100)

            print(data)


if __name__ == "__main__":
    m = MotorController("COM5")
    m.test()
