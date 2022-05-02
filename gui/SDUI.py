import sys
import cv2
import numpy as np

from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QHBoxLayout

from audio.python_receiver.receiver import Receiver
from audio.python_receiver.audio_sound_finder import SoundFinder 
from imaging.haarCascadeWArduino import angle_calculation
from imaging.videoCaptureClass import VideoCapture


class AudioThread(QThread):
    audio_angle_signal = pyqtSignal(float)

    def __init__(self, audio_mcu, soundfinder_settings):
        super().__init__()
        self._run_flag = True
        self.audio_mcu = audio_mcu
        self.sfs = soundfinder_settings

    def run(self):
        r = Receiver(self.audio_mcu, use_file=False)
        sf = SoundFinder(r,
            self.sfs['sampling_rate'], self.sfs['frame_size'],
            self.sfs['mic_distance'], self.sfs['normalize_signal'],
            [self.sfs['filter_lowcut'], self.sfs['filter_highcut'], self.sfs['filter_order'], self.sfs['filter_ratio'], self.sfs['filter_bands'], self.sfs['filter_graph'], self.sfs['filter_bands_avg_ratio'], self.sfs['filter_bands_order']] if self.sfs['filter_on'] else None,
            self.sfs['average_delays'], self.sfs['left_mic'],
            [self.sfs['angle_middle_calib'], self.sfs['angle_edge_calib']],
            self.sfs['log_output'], self.sfs['graph_samples'])

        while self._run_flag:
            audioAngle = 90
            # imagingAngle = 90
            # finalAngle = 90
            sfAngle, sfMic = sf.next_angle()  # get next/current angle
            audioAngle = sf.convert_angle(sfAngle, sfMic)
            audioAngle = 90

            self.audio_angle_signal.emit(audioAngle)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
class ImagingThread(QThread):
    people_angles_signal = pyqtSignal(list)
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, imaging_camera, max_imaged_people):
        super().__init__()
        self._run_flag = True
        self.imaging_camera = imaging_camera
        self.max_imaged_people = max_imaged_people
        self.videoCapture = None

    def run(self):
        self.videoCapture = VideoCapture(self.imaging_camera, False, self.change_pixmap_signal)
        array_private = [-1 for i in range(self.max_imaged_people)]
        while self._run_flag:
            array_private = [-1 for i in range(self.max_imaged_people)]
            verifiedPeople = self.videoCapture.run()
            i = 0
            for person in verifiedPeople:
                array_private[i] = angle_calculation(person.x)
                # print(f"{person} with angle {angle_calculation(person.x)}")
                i = i + 1
            self.people_angles_signal.emit(array_private)

    def stop(self):
        self._run_flag = False
        self.wait()

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, viewing_camera):
        super().__init__()
        self._run_flag = True
        self.viewing_camera = viewing_camera

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(self.viewing_camera)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()



class App(QWidget):
    def __init__(self, viewing_camera, imaging_camera, audio_mcu, motor_mcu, max_imaged_people, soundfinder_settings):
        super().__init__()
        self.setWindowTitle("Where Is The Sound")
        self.display_width = 1280
        self.display_height = 700
        # people angles list
        self.people_angle_list = []
        # create the label that holds the image
        self.image_height_offset = 315
        self.image_width = self.display_width / 2
        self.image_height = self.display_height - self.image_height_offset
        self.image_label = QLabel(self)
        self.image_label.resize(self.image_width,self.image_height)
        self.image_label_2 = QLabel(self)
        self.image_label_2.resize(self.image_width,self.image_height)

        # create a text label
        self.textLabel = QLabel('Webcam')

        # create a vertical box layout and add the two labels
        self.vbox = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.image_label)
        self.hbox.addWidget(self.image_label_2)
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.textLabel)
        # set the vbox layout as the widgets layout
        self.setLayout(self.vbox)

        # create the audio analysis thread
        self.audio_thread = AudioThread(audio_mcu, soundfinder_settings)
        # connect its signal to the update_image slot
        self.audio_thread.audio_angle_signal.connect(self.update_audio_angle)
        # start the thread
        self.audio_thread.start()

        # create the video capture thread
        self.video_thread = VideoThread(viewing_camera)
        # connect its signal to the update_image slot
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.video_thread.start()

        # create the imaging capture thread
        self.img_thread = ImagingThread(imaging_camera, max_imaged_people)
        # connect its signal to the update_image slot
        self.img_thread.change_pixmap_signal.connect(self.update_image_2)
        self.img_thread.people_angles_signal.connect(self.update_people)
        # start the thread
        self.img_thread.start()

    def closeEvent(self, event):
        self.video_thread.stop()
        self.img_thread.stop()
        event.accept()


    @pyqtSlot(float)
    def update_audio_angle(self, audio_angle):
        self.trigger_angle_update(audio_angle, self.people_angle_list)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
        self.image_label.resize(640,480)

    @pyqtSlot(np.ndarray)
    def update_image_2(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label_2.setPixmap(qt_img)
        self.image_label_2.resize(640,480)

    @pyqtSlot(list)
    def update_people(self, people_angles):
        # print("people angles: ", end="")
        # print("[ ", end="")
        public_arr = []
        for a in people_angles:
            if a == -1: continue
            public_arr.append(a)
        #     print("{} ".format(a), end="")
        # print("] ")
        self.people_angle_list = public_arr
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.image_width, self.image_height, Qt.KeepAspectRatio)
        p = convert_to_Qt_format.scaled(self.image_width, self.image_height)
        return QPixmap.fromImage(p)

    def trigger_angle_update(self, audio_angle, people_angles):
        print("audio_angle={}, people_angles={}".format(audio_angle, people_angles))
        # pass
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())