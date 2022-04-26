import sys
import time
import numpy as np
from numpy import inf
from multiprocessing import Process, Value, Array
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

from audio.python_receiver.receiver import Receiver
from audio.python_receiver.audio import SoundFinder 
from imaging.videoCaptureClass import VideoCapture
from imaging.haarCascadeWArduino import angle_calculation
from motors.motor_controller import MotorController
from gui.SDUI import App


audio_mcu = "/dev/cu.SLAB_USBtoUART"
motor_mcu = "/dev/cu.usbmodem0E22BD701"  # COM5
imaging_camera = 2
viewing_camera = 1

videoCapture = VideoCapture(imaging_camera)
def imagingFunc(array):
    array_private = [-1,-1,-1]
    while True:
        array_private = [-1,-1,-1]
        verifiedPeople = videoCapture.run()
        i=0
        for person in verifiedPeople:
            array_private[i] = angle_calculation(person.x)
            print(f"{person} with angle {angle_calculation(person.x)}")
            i=i+1     
        i = 0   
        for angle in array_private:
            array[i] = array_private[i]
            i = i + 1

def audioFunc(sf):
    while True:
        angle = sf.next_angle()  # get next/current angle
        print(f"audio angle: {angle}")

if __name__ == "__main__":

     # audio sampling & correlation settings
    source_use_file = False   # use device or file
    source = audio_mcu if not source_use_file else r"audio\python_receiver\data\sample_gen_example1_32kHz_800Hz_0.0001ms.txt"
    sampling_rate = 32        # kHz  -  MUST MATCH ESP
    frame_size = 768          # #samples  -  MUST MATCH ESP
    mic_distance = 250        # mm  -  MUST MATCH SETUP
    average_delays = 2       # rolling average on sample delay (set to 0 for none)
    normalize_signal = True   # normalize before correlation
    filter_on = True          # butterworth bandpass filter
    filter_lowcut = 400.0     # Hz
    filter_highcut = 1400.0   # Hz
    filter_order = 12         # filter order
    #repeat = True             # sample forever or only once
    graph_samples = True      # generate plot (takes more time)
    angle_edge_calib = 25  #25 # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45)
    angle_middle_calib = 90   # observed incident angle middle (should be 90)
    left_mic = 'mic_A'
    log_output = False         # log the output
    frame_length = frame_size / (sampling_rate * 1000)  # sec

    r = Receiver(source, use_file=source_use_file)
    sf = SoundFinder(r, sampling_rate, frame_size, mic_distance, normalize_signal, [filter_lowcut, filter_highcut, filter_order], average_delays, left_mic, [angle_middle_calib, angle_edge_calib], log_output, graph_samples)

    m = MotorController(motor_mcu)
    m.move(0)   # center the camera

    arr = Array('d', [-1,-1,-1])
    p1 = Process(target=imagingFunc, args=(arr,))
    #p2 = Process(target=audioFunc, args=(sf,))
    p1.start()
    #p2.start()
    #p1.join()
    #p2.join()

    app = QApplication(sys.argv)
    a = App()
    a.show()

    rolling_average_angles = []

    while True:
        angle, mic = sf.next_angle()  # get next/current angle
        angle = sf.convert_angle(angle, mic)
        print(f"audio angle: {angle}")
        bestDiff = inf
        bestAngle = 90
        for person in arr:
            if person == -1: continue
            # print(angle)
            diff = abs(angle - person)
            if diff < bestDiff:
                bestDiff = diff
                bestAngle = person
            # print(person)
        # bestAngle = angle
        print('audio_angle={}'.format(angle))
        print('imaging_angle={}'.format(bestAngle))
        bestAngle = int(round(bestAngle * 10, 0))
        # bestAudioAngle = int(round(angle * 10, 0))
        # bestAngle = (0.75 * bestAngle + 0.25 * bestAudioAngle)
        rolling_average_angles.append(bestAngle)
        if len(rolling_average_angles) >= 3:
            rolling_average_angles = rolling_average_angles[1:]
        final_angle = np.mean(rolling_average_angles)
        print(rolling_average_angles)
        final_angle = int(final_angle)
        print(f"final angle is {final_angle}")
        m.move(final_angle)
        # time.sleep(2)


    sys.exit(app.exec_())

