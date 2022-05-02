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
from audio.python_receiver.audio_sound_finder import SoundFinder 
from imaging.videoCaptureClass import VideoCapture
from imaging.haarCascadeWArduino import angle_calculation
from motors.motor_controller import MotorController
from gui.SDUI import App


# input settings
audio_mcu = "/dev/cu.SLAB_USBtoUART"
motor_mcu = "/dev/cu.usbmodem0E22BD701"  # COM5
imaging_camera = 1  # 2
viewing_camera = 0  # 1
max_imaged_people = 20
motor_enable = False
imaging_audio_ratio = 70
rolling_average_angles_num = 2
maximum_imaging_audio_diff = 75
maximum_straddling_angle_diff = 15

# audio sampling & correlation settings
source_use_file = False   # use device or file
source = audio_mcu if not source_use_file else r"audio\python_receiver\data\sample_gen_example1_32kHz_800Hz_0.0001ms.txt"
sampling_rate = 16        # kHz  -  MUST MATCH ESP              (ideal = 16 or 32)
frame_size = 512          # #samples  -  MUST MATCH ESP         (ideal = 512 or 1024)
mic_distance = 250        # mm  -  MUST MATCH SETUP             (ideal = 75mm, 250mm, 500mm, 1000mm)
average_delays = 3        # rolling average on sample delay (0 for none) (ideal = 3 --> for more stability in values as well as smoother range)
normalize_signal = True   # normalize before correlation        (ideal = True)
filter_on = True          # butterworth bandpass filter         (ideal = True)
filter_lowcut = 500.0     # Hz                                  (ideal = 400-500)
filter_highcut = 1200.0   # Hz                                  (ideal = 1200-1400)
filter_order = 4          # filter order                        (ideal = 4 for filtfilt, 8 for sosfiltfilt)
filter_ratio = 30         # %                                   (ideal = 20-30)
filter_bands_order = 6
# filter_bands = None
filter_bands = [ [550,750], [650,850], [400,500], [500,600], [600,700], [700,800], [800,900], [900,1000] ]
filter_bands_avg_ratio = 10 # %                                 (ideal = 15-20)
filter_graph = False      # display filtered or unfiltered signal frame on graph
repeat = True             # sample forever or only once
graph_samples = False     # generate plot (takes more time)
angle_edge_calib = 25     # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45) (ideal = 25)
angle_middle_calib = 90   # observed incident angle middle (should be 90)
log_output = False        # log the output
left_mic = 'mic_A'        # which mic is on the left  (usually = 'mic_A')
frame_length = frame_size / (sampling_rate * 1000)  # sec

videoCapture = VideoCapture(imaging_camera)
def imagingFunc(array):
    array_private = [-1 for i in range(max_imaged_people)]
    while True:
        array_private = [-1 for i in range(max_imaged_people)]
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

def interfaceFunc():
    run_view = True
    app = QApplication(sys.argv)
    a = App()
    a.show()
    try:
        while run_view:
            pass
    except:
        sys.exit(app.exec_())
    


# def audioFunc(sf):
#     while True:
#         angle = sf.next_angle()  # get next/current angle
#         print(f"audio angle: {angle}")

if __name__ == "__main__":

    main_run = True

    r = Receiver(source, use_file=source_use_file)
    sf = SoundFinder(r, sampling_rate, frame_size, mic_distance, normalize_signal, [filter_lowcut, filter_highcut, filter_order, filter_ratio, filter_bands, filter_graph, filter_bands_avg_ratio, filter_bands_order] if filter_on else None, average_delays, left_mic, [angle_middle_calib, angle_edge_calib], log_output, graph_samples)

    m = None
    if motor_enable:
        m = MotorController(motor_mcu)
        m.move(0)   # center the camera

    arr = Array('d', [-1 for i in range(max_imaged_people)])
    p1 = Process(target=imagingFunc, args=(arr,))
    # p2 = Process(target=interfaceFunc, args=())
    p1.start()
    # p2.start()

    rolling_average_angles = []
    maxDiff = maximum_imaging_audio_diff

    while main_run:

        audioAngle = 90
        imagingAngle = 90
        finalAngle = 90

        sfAngle, sfMic = sf.next_angle()  # get next/current angle
        audioAngle = sf.convert_angle(sfAngle, sfMic)
        audioAngle = 90

        numImgPeople = 0
        bestImgDiff = inf
        bestImgAngle = audioAngle
        secondBestImgDiff = inf
        secondBestImgAngle = audioAngle
        print("[", end='')
        for personAngle in arr:
            if personAngle == -1: continue
            numImgPeople += 1
            print("{}, ".format(personAngle), end='')
            diff = abs(audioAngle - personAngle)
            if diff < bestImgDiff:  # and diff < maxDiff:
                bestImgDiff = diff
                bestImgAngle = personAngle
            elif diff < secondBestImgDiff:  # and diff < maxDiff:
                secondBestImgDiff = diff
                secondBestImgAngle = personAngle
            # print('angle={},diff={}'.format(angle,diff))
        print("] --> {}".format(numImgPeople))
        if numImgPeople == 0:
            imagingAngle = audioAngle
        elif numImgPeople == 1:
            imagingAngle = bestImgAngle
            # imagingAngle = arr[0]
        elif numImgPeople >= 2:
            if bestImgDiff <= maximum_straddling_angle_diff and secondBestImgDiff <= maximum_straddling_angle_diff:
                imagingAngle = (bestImgDiff + secondBestImgDiff) / 2
            else:
                imagingAngle = bestImgAngle

        finalAngle = ((imaging_audio_ratio / 100) * imagingAngle) + ((1 - (imaging_audio_ratio / 100)) * audioAngle)
        # print('audio_angle={}'.format(audioAngle))
        # print('imaging_angle={}'.format(imagingAngle))
        print(f"final angle={finalAngle}")

        rolling_average_angles.append(finalAngle)
        if len(rolling_average_angles) > rolling_average_angles_num:
            rolling_average_angles = rolling_average_angles[1:]
        finalAngle = np.mean(rolling_average_angles)
        # print(rolling_average_angles)
        # print(f"averaged angle is {finalAngle}")

        if motor_enable:
            motorAngle = int(round(finalAngle * 10, 0))
            m.move(motorAngle)
        
        # time.sleep(2)

    
    p1.join()
    # p2.join()


    

