import numpy as np
import serial
import time

class Receiver:
    """
    Receives data from microcontroller
    """
    source = None
    use_file = None
    baud_rate = None
    serial_port = None


    def __init__(self, source: str, use_file=False, baud_rate=115200) -> np.array:
        """
        Connects to device, receives a number of samples, and returns them
        """

        self.source = source
        self.use_file = use_file
        self.baud_rate = baud_rate
        if self.use_file is True:
            self.serial_port = open(self.source, "rb")
        else:
            self.serial_port = serial.Serial(self.source, self.baud_rate, timeout=1, write_timeout=1)
            # self.serial_port.write("f{num_samples}".encode('utf-8'))

    def receive(self, num_samples: int) -> np.array:
        """
        Receives specified number of lines of data
        """

        i = 0
        data = np.zeros((num_samples, 3), dtype=np.uint)


        self.serial_port.flushInput()

        # Wait for the start character
        while True:
            data_line = self.serial_port.readline()
            print(data_line)
            raw_data = data_line.split()
            print(raw_data)

            # print(raw_data[0])
            # print(raw_data)
            if len(raw_data) >= 1 and raw_data[0] == b's':
                break
            
        while i < num_samples:


            raw_data = self.serial_port.readline().split()  # blocking
            # print(raw_data)
            data[i] = raw_data  # blocking
            # print(data[i])
            i = i + 1

        # s.close()

        return data


if __name__ == "__main__":
    # r = Receiver("test_data", use_file=True)

    # data = r.receive(10)

    # print(data)

    r = Receiver("/dev/cu.usbmodem0E21FD801")

    while True:
        data = r.receive(128)
        print(data)
        # time.sleep(2)

    np.savetxt("run1", data, delimiter=" ")
