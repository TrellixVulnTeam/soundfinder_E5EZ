from __future__ import print_function
import cv2 as cv
import argparse
import time

class Person: 
    verifiedCounter = 1
    potentialCounter = 1
    verifiedArray = []
    potentialArray = []
    def __init__(self, x, y, w, h, verified, timeFirstDetected, timeLastDetected, countDetected, totalCounts, percentDetected): 
        self.id = 0
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.verified = verified
        if(verified):
            self.id = Person.verifiedCounter
            Person.verifiedCounter += 1
            Person.verifiedArray.append(self.id)
        else:
            self.id = Person.potentialCounter
            Person.potentialCounter += 1
            Person.potentialArray.append(self.id)
        self.seenThisRound = False
        self.timeFirstDetected = timeFirstDetected
        self.timeLastDetected = timeLastDetected
        self.countDetected = countDetected
        self.totalCounts = totalCounts
        self.percentDetected = percentDetected
    def __str__(self): 
        if(self.verified):
            return f"Verified Person {self.id}: x: {self.x} y: {self.y}"
        else:
            return f"Potential Person {self.id}: x: {self.x} y: {self.y}"


# Function to update seenThisRound, timeLastDetected, countDetected, totalCounts, percentDetected
# Given a person and one variable: either +1 for detected or -1 for not detected 
def updatePersonStats(person, one): 
    person.countDetected += one
    person.totalCounts += 1
    person.percentDetected = person.countDetected / person.totalCounts
    person.seenThisRound = 
# Create people array
# Criteria: 
# Person if has been detected 90% of the time for > 3 seconds
# Continues to be a person detected until
# Not detected 90% of the time for 3 seconds
# Distance: 3% variablity, aka 100 and 103 are same person
# Given x, y, w, h
# TESTING SINCE CLOSE: 20% variability
potentialPeople = []
verifiedPeople = []
smallPercent = .8
largePercent = 1.2
seconds = 3
def updateArrays(x, y, w, h, potentialPeople, verifiedPeople):
    # ADDING
    # Check if coordinates are already in verifiedPeople array
    smallX = smallPercent * x
    largeX = largePercent * x
    smallY = smallPercent * y
    largeY = largePercent * y
    alreadyVerified = False
    for person in verifiedPeople: 
        if(smallX < person.x < largeX and smallY < person.y < largeY): 
            alreadyVerified = True
            break
    # If already verified
    #   Increase their countDetected and totalCounts and percentDetected, then break out of function
    # If not, check if coordinates are already in potentialPeople
    #   If already in, increase their count detected and totalCounts
    #   If not, add them into potentialPeople
    if(alreadyVerified):
        for person in potentialPeople: 
            if(smallX < person.x < largeX and smallY < person.y < largeY): 

    else:  
        alreadyPotential = False
        for person in potentialPeople: 
            if(smallX < person.x < largeX and smallY < person.y < largeY): 
                alreadyPotential = True
                person.countDetected += 1
                person.totalCounts += 1
                person.percentDetected = person.countDetected / person.totalCounts
        if not alreadyPotential: 
            newPotentialPerson = potentialPerson(x, y, w, h, time.time(), 1, 1, 1)
            potentialPeople.append(newPotentialPerson)
    # Check if any people in potentialPeople should be in verifiedPeople
    # Not already verified, Time lived >= 3 seconds, and percentDetected > 90%  
    for person in potentialPeople: 
        # Make sure not already in verifiedPeople 
        if( not person.verified and time.time() - person.timeDetected >= 3 and person.percentDetected >= .9):
            verifiedPeople.append(Person(person.id, person.x, person.y, person.w, person.h))
            person.verified = True
    # DELETING 
    # Add a time since last detection, so you can check it's been more than 3 seconds
    # Add a verifiedThisRound so you can update counts and check if anyone disqualifies
    # Check potentialPeople and verifiedPeople if time since last detection > 3 or percentDetected < 90% 
    # Create only one person since verified needs more stats to determine deletion, you can include a param that says if verified or not
    # and using that param for count and any other specifics


def detectAndDisplay(frame):
    # greyscale for faster detection
    frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame_gray = cv.equalizeHist(frame_gray)

    height, width, channels = frame.shape

    #-- Detect faces
    faces = face_cascade.detectMultiScale(frame_gray, 1.1, 2)
    # faceFound = False
    for (x,y,w,h) in faces:
        # faceFound = True
        center = (x + w//2, y + h//2)
        # Args: 
        # 0: img, 1: Point center, 2: Size axes, 3: double angle, 4: double startAngle, 5: double endAngle
        # 6: const Scalar & color
        frame = cv.ellipse(frame, center, (w//2, h//2), 0, 0, 360, (255, 0, 255), 4)
        # Create person array
        updateArrays(x, y, w, h, potentialPeople, verifiedPeople)

    # for person in verifiedPeople: 
    #     print(person)
    # Detect upper bodies
    bodies = body_cascade.detectMultiScale(frame_gray, 
        scaleFactor = 1.1,
        minNeighbors =  2, 
        minSize = (50, 100), 
        flags = cv.CASCADE_SCALE_IMAGE
    )
    bodyFound = False
    for(x,y,w,h) in bodies:
        bodyFound = True
        frame = cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        

    # # Zooming
    # if(bodyFound):
    #     try: 
    #         minX = x+(w//2)-100
    #         maxX = x+(w//2)+100
    #         minY = y+(h//2)-100
    #         maxY = y+(h//2)+100
    #         cropped = frame[minY:maxY, minX:maxX]
    #         resized_cropped = cv.resize(cropped, (width, height))
    #         cv.imshow('Capture - Face and body detection', resized_cropped)
    #     except Exception as e: 
    #         print(str(e))
    # else:
    #     cv.imshow('Capture - Face and body detection', frame)
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
for person in potentialPeople: 
    print(person)
for person in verifiedPeople: 
    print(person)
    