import numpy as np
import serial

class Receiver:
    """
    Receives data from microcontroller
    """
    source = None
    use_file = None
    baud_rate = None



    def __init__(self, source: str, use_file=False, baud_rate=115200) -> np.array:
        """
        Connects to device, receives a number of samples, and returns them
        """

        self.source = source
        self.use_file = use_file
        self.baud_rate = baud_rate

    def receive(self, num_samples: int) -> np.array:
        """
        Receives specified number of lines of data
        """
        s = None
        if self.use_file is True:
            s = open(self.source, "rb")
        else:
            s = serial.Serial(self.source, self.baud_rate, timeout=1, write_timeout=1)
            # s.write("f{num_samples}".encode('utf-8'))

        i = 0
        data = np.zeros((num_samples, 3), dtype=np.uint)


        # Wait for the start character
        while True:
            raw_data = s.readline().split()

            # print(raw_data[0])
            print(raw_data)
            if raw_data[0] == b's':
                break
            
        while i < num_samples:


            raw_data = s.readline().split()  # blocking
            # print(raw_data)
            data[i] = raw_data  # blocking
            # print(data[i])
            i = i + 1

        s.close()

        return data


if __name__ == "__main__":
    # r = Receiver("test_data", use_file=True)

    # data = r.receive(10)

    # print(data)

    r = Receiver("COM27")

    data = r.receive(10)
    print(data)

    np.savetxt("run1", data, delimiter=" ")
