import sys
import cv2
import numpy as np

from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QHBoxLayout

from audio.transcription.transcribe import TranscriptionClient
from audio.python_receiver.receiver import Receiver
from audio.python_receiver.audio_sound_finder import SoundFinder
from imaging.haarCascadeWArduino import angle_calculation
from motors.motor_controller import MotorController
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
            [self.sfs['filter_lowcut'], self.sfs['filter_highcut'],
                self.sfs['filter_order'], self.sfs['filter_ratio'], self.sfs['filter_bands'],
                self.sfs['filter_graph'], self.sfs['filter_bands_avg_ratio'],
                self.sfs['filter_bands_order']] if self.sfs['filter_on'] else None,
            self.sfs['average_delays'], self.sfs['left_mic'],
            [self.sfs['angle_middle_calib'], self.sfs['angle_edge_calib']],
            self.sfs['log_output'], self.sfs['graph_samples'])

        while self._run_flag:
            audioAngle = 90
            # imagingAngle = 90
            # finalAngle = 90
            sfAngle, sfMic = sf.next_angle()  # get next/current angle
            # print("***** {} {}".format(sfAngle, sfMic))
            audioAngle = sf.convert_angle(sfAngle, sfMic)
            # audioAngle = 90

            self.audio_angle_signal.emit(audioAngle)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

class ImagingThread(QThread):
    people_angles_signal = pyqtSignal(list)
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, imaging_camera, max_imaged_people, face_detect_interval = 3):
        super().__init__()
        self._run_flag = True
        self.imaging_camera = imaging_camera
        self.max_imaged_people = max_imaged_people
        self.videoCapture = None
        self.face_detect_interval = face_detect_interval

    def run(self):
        self.videoCapture = VideoCapture(self.imaging_camera, False, self.change_pixmap_signal, self.face_detect_interval)
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
    people_angles_signal = pyqtSignal(list)
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, viewing_camera, max_imaged_people, face_detect_interval = 3):
        super().__init__()
        self._run_flag = True
        self.viewing_camera = viewing_camera

        self.videoCapture = None
        self.max_imaged_people = max_imaged_people
        self.face_detect_interval = face_detect_interval

    def run(self):
        # # capture from web cam
        # cap = cv2.VideoCapture(self.viewing_camera)
        # while self._run_flag:
        #     ret, cv_img = cap.read()
        #     if ret:
        #         self.change_pixmap_signal.emit(cv_img)
        # # shut down capture system
        # cap.release()
        self.videoCapture = VideoCapture(self.viewing_camera, False, self.change_pixmap_signal, self.face_detect_interval)
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
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

class TranscriptionThread(QThread):
    update_caption_line = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.transcription_client = None

    def run(self):
        self.transcription_client = TranscriptionClient(self.update_caption_line, False)
        while self._run_flag:
            try:
                self.transcription_client.transcribe()
            except:
                if not self._run_flag:
                    return

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.transcription_client.stop()
        self.wait()



class App(QWidget):
    def __init__(self, viewing_camera, imaging_camera, audio_mcu, motor_mcu, max_imaged_people, soundfinder_settings, imaging_audio_ratio, rolling_average_angles_num, maximum_imaging_audio_diff, maximum_straddling_angle_diff, face_detect_interval, secondary_imaging_ratio):
        super().__init__()
        self.setWindowTitle("Where Is The Sound")
        self.display_width = 1280
        self.display_height = 700
        # people angles list
        self.people_angle_list = []
        self.people_secondary_angle_list = []
        self.rolling_average_angles = []
        self.sfs = soundfinder_settings
        self.max_imaged_people = max_imaged_people
        self.imaging_audio_ratio = imaging_audio_ratio
        self.rolling_average_angles_num = rolling_average_angles_num
        self.maximum_imaging_audio_diff = maximum_imaging_audio_diff
        self.maximum_straddling_angle_diff = maximum_straddling_angle_diff
        self.secondary_imaging_ratio = secondary_imaging_ratio
        self.motor_mcu = motor_mcu
        self.motor_controller = None
        self.audio_angle = 0
        # create the label that holds the image
        self.image_height_offset = 315
        self.image_width = self.display_width / 2
        self.image_height = self.display_height - self.image_height_offset
        self.image_label = QLabel(self)
        self.image_label.resize(self.image_width,self.image_height)
        self.image_label_2 = QLabel(self)
        self.image_label_2.resize(self.image_width,self.image_height)

        # create a text label
        self.textLabel = QLabel('Where Is The Sound?')
        self.textLabel.setAlignment(Qt.AlignCenter)


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
        self.video_thread = VideoThread(viewing_camera, max_imaged_people, face_detect_interval)
        # connect its signal to the update_image slot
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.people_angles_signal.connect(self.update_people_secondary)
        # start the thread
        self.video_thread.start()

        # create the imaging capture thread
        self.img_thread = ImagingThread(imaging_camera, max_imaged_people, face_detect_interval)
        # connect its signal to the update_image slot
        self.img_thread.change_pixmap_signal.connect(self.update_image_2)
        self.img_thread.people_angles_signal.connect(self.update_people)
        # start the thread
        self.img_thread.start()

        # create the transcription thread
        self.tc_thread = TranscriptionThread()
        # connect its signal to the update_image slot
        self.tc_thread.update_caption_line.connect(self.update_transcription)
        # start the thread
        self.tc_thread.start()

        # start motor control
        if self.motor_mcu != None:
            self.motor_controller = MotorController(self.motor_mcu)
            self.motor_controller.move(0)   # center the camera

    def closeEvent(self, event):
        self.audio_thread.stop()
        self.video_thread.stop()
        self.img_thread.stop()
        self.tc_thread.stop()
        event.accept()

    def update_motor_angle(self, motor_angle):
        motor_angle = int(round(motor_angle * 10, 0))
        print("motor angle = {}".format(motor_angle))
        if self.motor_mcu != None and self.motor_controller != None:
            self.motor_controller.move(motor_angle)

    @pyqtSlot(float)
    def update_audio_angle(self, audio_angle):
        self.audio_angle = audio_angle
        self.trigger_angle_update(audio_angle, self.people_angle_list, self.people_secondary_angle_list)

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
        self.trigger_angle_update(self.audio_angle, public_arr, self.people_secondary_angle_list)

    @pyqtSlot(list)
    def update_people_secondary(self, people_angles_secondary):
        # print("secondary people angles: ", end="")
        # print("[ ", end="")
        public_arr = []
        for a in people_angles_secondary:
            if a == -1: continue
            public_arr.append(a)
        #     print("{} ".format(a), end="")
        # print("] ")
        self.people_secondary_angle_list = public_arr
        self.trigger_angle_update(self.audio_angle, self.people_angle_list, public_arr)
    
    @pyqtSlot(str)
    def update_transcription(self, caption_line):
        print("captions: '{}'".format(caption_line))
        self.textLabel.setText((str(caption_line)).replace(". ", ".  "))
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.image_width, self.image_height, Qt.KeepAspectRatio)
        p = convert_to_Qt_format.scaled(self.image_width, self.image_height)
        return QPixmap.fromImage(p)

    def trigger_angle_update(self, audio_angle, people_angles, people_angles_secondary = []):
        print("audio_angle={}\npeople_angles={}\npeople_angles_secondary={}".format(audio_angle, people_angles, people_angles_secondary))
        numImgPeople = 0
        bestImgDiff = np.inf
        bestImgAngle = audio_angle
        secondBestImgDiff = np.inf
        secondBestImgAngle = audio_angle
        # print("[", end='')
        for personAngle in people_angles:
            if personAngle == -1: continue
            numImgPeople += 1
            # print("{}, ".format(personAngle), end='')
            diff = abs(audio_angle - personAngle)
            if diff < bestImgDiff:  # and diff < maxDiff:
                bestImgDiff = diff
                bestImgAngle = personAngle
            elif diff < secondBestImgDiff:  # and diff < maxDiff:
                secondBestImgDiff = diff
                secondBestImgAngle = personAngle
            # print('angle={},diff={}'.format(angle,diff))
        # print("] --> {}".format(numImgPeople))
        if numImgPeople == 0:
            imagingAngle = audio_angle
        elif numImgPeople == 1:
            imagingAngle = bestImgAngle
            # imagingAngle = arr[0]
        elif numImgPeople >= 2:
            if bestImgDiff <= self.maximum_straddling_angle_diff and secondBestImgDiff <= self.maximum_straddling_angle_diff:
                imagingAngle = (bestImgAngle + secondBestImgAngle) / 2
            else:
                imagingAngle = bestImgAngle

        finalAngle = ((self.imaging_audio_ratio / 100) * imagingAngle) + ((1 - (self.imaging_audio_ratio / 100)) * audio_angle)
        # print('audio_angle={}'.format(audioAngle))
        # print('imaging_angle={}'.format(imagingAngle))
        # print(f"final angle={finalAngle}")

        # modify with second camera's imaging
        closestToMiddle = -1
        minDiff = np.inf
        if len(people_angles_secondary) > 0:
            for secondaryPersonAngle in people_angles_secondary:
                diff = abs(secondaryPersonAngle - 90)
                if diff < minDiff:
                    minDiff = diff
                    closestToMiddle = secondaryPersonAngle
            finalAngle += (closestToMiddle - 90) * (self.secondary_imaging_ratio / 100)
        

        self.rolling_average_angles.append(finalAngle)
        if len(self.rolling_average_angles) > self.rolling_average_angles_num:
            self.rolling_average_angles = self.rolling_average_angles[1:]
        finalAngle = np.mean(self.rolling_average_angles)

        self.update_motor_angle(finalAngle)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())