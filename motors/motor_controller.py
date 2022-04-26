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
        # time.sleep(1)

        # self.t1 = Thread(target=self.listen)
        # self.t1.start()

    def move(self, angle: int):
        """
        Moves motor to a specified position
        Angle in increments of a tenth of a degree and can be between -900 and 900
        :param angle:   The angle to move to in tenths of degree. So to move to 45, send 450
        """

        if angle < -900 or angle > 900:
            raise ValueError("Angle cannot be below -900 or above 900")

        if angle < 0:
            self.r.write(b'B')
            time.sleep(0.1)
            self.r.write(f'{angle}\r'.encode('utf-8'))
        else:
            self.r.write(b'A')
            time.sleep(0.1)
            self.r.write(f'{angle}\r'.encode('utf-8'))

    def test(self):
        self.r.write(b"Poggers\n")
        print("Wrote poggers")

    def listen(self):
        while True:
            data = self.r.read(100)

            print(data)


if __name__ == "__main__":
    m = MotorController("/dev/cu.usbmodem0E22BD701")

    m.move(-500)

    # for i in range(-900, 900, 100):
    #     m.move(i)
    #     time.sleep(0.25)

    # for i in range(900, -900, 100):
    #     m.move(i)
    #     time.sleep(0.25)
