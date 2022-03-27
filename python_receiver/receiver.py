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
            s = serial.Serial(self.source, self.baud_rate)

        i = 0
        data = np.zeros((num_samples, 3), dtype=np.uint)

        while i < num_samples:
            data[i] = s.readline().split()  # blocking
            i = i + 1

        s.close()

        return data


if __name__ == "__main__":
    r = Receiver("random_data", use_file=True)

    data = r.receive(10)

    print(data)