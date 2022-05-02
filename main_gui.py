import sys
import time
import numpy as np
from numpy import inf
from multiprocessing import Process, Value, Array
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

from audio.transcription import transcribe
from audio.python_receiver.receiver import Receiver
from audio.python_receiver.audio_sound_finder import SoundFinder
from imaging.videoCaptureClass import VideoCapture
from imaging.haarCascadeWArduino import angle_calculation
from motors.motor_controller import MotorController
from gui.SDUI import App


# input settings
audio_mcu = "/dev/cu.SLAB_USBtoUART"
motor_mcu = "/dev/cu.usbmodem0E22BD701"  # COM5
# motor_mcu = None
imaging_camera = 2  # 2
viewing_camera = 1  # 1
max_imaged_people = 20
motor_enable = False
imaging_audio_ratio = 60  # was 70
secondary_imaging_ratio = 20  # try diff amounts
rolling_average_angles_num = 2
maximum_imaging_audio_diff = 75
maximum_straddling_angle_diff = 15
face_detect_interval = 4 # 3-4 by default
soundfinder_settings = {
    "sampling_rate": 16,        # kHz  -  MUST MATCH ESP              (ideal": 16 or 32)
    "frame_size": 512,          # #samples  -  MUST MATCH ESP         (ideal": 512 or 1024)
    "mic_distance": 250,        # mm  -  MUST MATCH SETUP             (ideal": 75mm, 250mm, 500mm, 1000mm)
    "average_delays": 3,        # rolling average on sample delay (0 for none) (ideal": 3 --> for more stability in values as well as smoother range)
    "normalize_signal": True,   # normalize before correlation        (ideal": True)
    "filter_on": True,          # butterworth bandpass filter         (ideal": True)
    "filter_lowcut": 500.0,     # Hz                                  (ideal": 400-500)
    "filter_highcut": 1200.0,   # Hz                                  (ideal": 1200-1400)
    "filter_order": 4,          # filter order                        (ideal": 4 for filtfilt, 8 for sosfiltfilt)
    "filter_ratio": 30,         # %                                   (ideal": 20-30)
    "filter_bands_order": 6,
    # "filter_bands": None,
    "filter_bands": [ [550,750], [650,850], [400,500], [500,600], [600,700], [700,800], [800,900], [900,1000] ],
    "filter_bands_avg_ratio": 10, # %                                 (ideal": 15-20)
    "filter_graph": False,      # display filtered or unfiltered signal frame on graph
    "repeat": True,             # sample forever or only once
    "graph_samples": False,     # generate plot (takes more time)
    "angle_edge_calib": 25,     # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45) (ideal": 25)
    "angle_middle_calib": 90,   # observed incident angle middle (should be 90)
    "log_output": True,        # log the output
    "left_mic": 'mic_B',        # which mic is on the left  (usually": 'mic_A', currently 'mic_B')
}

if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App(viewing_camera, imaging_camera, audio_mcu, motor_mcu, max_imaged_people, soundfinder_settings, imaging_audio_ratio, rolling_average_angles_num, maximum_imaging_audio_diff, maximum_straddling_angle_diff, face_detect_interval, secondary_imaging_ratio)
    a.show()
    # block
    sys.exit(app.exec_())