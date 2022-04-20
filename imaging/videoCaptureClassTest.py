from videoCaptureClass import VideoCapture

videoCapture = VideoCapture()
# Everytime it's called, takes 4 seconds to return a list of verified people
verifiedPeople = videoCapture.run()
for person in verifiedPeople:
    print(person)