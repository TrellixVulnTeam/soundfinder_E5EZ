from __future__ import print_function
import cv2 as cv
import argparse
def detectAndDisplay(frame):
    # greyscale for faster detection
    frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame_gray = cv.equalizeHist(frame_gray)
    #-- Detect faces
    faces = face_cascade.detectMultiScale(frame_gray, 1.1, 3)
    for (x,y,w,h) in faces:
        center = (x + w//2, y + h//2)
        frame = cv.ellipse(frame, center, (w//2, h//2), 0, 0, 360, (255, 0, 255), 4)
    # Detect upper bodies
    bodies = body_cascade.detectMultiScale(frame_gray, 
        scaleFactor = 1.1,
        minNeighbors =  3, 
        minSize = (50, 100), 
        flags = cv.CASCADE_SCALE_IMAGE
    )
    for(x,y,w,h) in bodies:
        frame = cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv.imshow('Capture - Face and body detection', frame)
face_cascade = cv.CascadeClassifier('C:/Users/ckaro/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0/LocalCache/local-packages/Python310/site-packages/cv2/data/haarcascade_frontalface_alt.xml')
body_cascade = cv.CascadeClassifier('C:/Users/ckaro/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0/LocalCache/local-packages/Python310/site-packages/cv2/data/haarcascade_upperbody.xml')
#-- 2. Read the video stream
cap = cv.VideoCapture(0)
if not cap.isOpened:
    print('--(!)Error opening video capture')
    exit(0)
while True:
    ret, frame = cap.read()
    # resizing for faster detection
    frame = cv.resize(frame, (640, 480))
    if frame is None:
        print('--(!) No captured frame -- Break!')
        break
    detectAndDisplay(frame)
    # if cv.waitKey(10) == 27:
    if cv.waitKey(1) & 0xFF == ord('q'):
        break