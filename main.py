from audio.python_receiver.receiver import Receiver
from imaging.videoCaptureClass import VideoCapture
from imaging.haarCascadeWArduino import angle_calculation

if __name__ == "__main__":
    videoCapture = VideoCapture()

    verifiedPeople = videoCapture.run()
    for person in verifiedPeople:
        print(f"{person} with angle {angle_calculation(person.x)}")

