from __future__ import print_function
import cv2 as cv
import argparse
import time

class Person: 
    verifiedCounter = 1
    potentialCounter = 1
    verifiedArray = []
    potentialArray = []
    def __init__(self, x, y, w, h, timeFirstDetected, timeLastDetected, seenThisRound, countDetected, totalCounts, percentDetected): 
        self.id = Person.potentialCounter
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.verified = False
        self.timeFirstDetected = timeFirstDetected
        self.timeLastDetected = timeLastDetected
        self.seenThisRound = seenThisRound
        self.countDetected = countDetected
        self.totalCounts = totalCounts
        self.percentDetected = percentDetected
        Person.potentialCounter += 1
        Person.potentialArray.append(self)
    def __str__(self): 
        if(self.verified):
            return f"Verified Person {self.id}: x: {self.x} y: {self.y}"
        else:
            return f"Potential Person {self.id}: x: {self.x} y: {self.y}"
    # Function to update timeLastDetected, countDetected, totalCounts, percentDetected, seenThisRound
    # Given a person and one variable: either +1 for detected or -1 for not detected 
    def updateStats(self, one):
        if(one == 1):
            timeLastDetected = time.time()
        self.countDetected += one
        self.totalCounts += 1
        self.percentDetected = self.countDetected / self.totalCounts
        self.seenThisRound = True
    def verifyPerson(self):
        self.verified  = True
        self.id = Person.verifiedCounter
        Person.verifiedCounter += 1
        Person.verifiedArray.append(self.id)


class VideoCapture:

    def __init__(self): 
        # distance = distance to qualify as same person
        # time = seconds where a face has to be > certain percent to qualify 
        # percent = percent of time a face has to be detected to qualify 
        self.distance = 50
        self.time = 3
        self.percent = .9

    # Returns array of people
    def run(self): 
        face_cascade = cv.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_frontalface_alt.xml')
        body_cascade = cv.CascadeClassifier('venv/Lib/site-packages/cv2/data/haarcascade_upperbody.xml')
        #-- 2. Read the video stream
        cap = cv.VideoCapture(0)
        if not cap.isOpened:
            print('--(!)Error opening video capture')
            exit(0)
        startTime = time.time()
        while time.time() - startTime < 4:
            ret, frame = cap.read()
            # resizing for faster detection
            frame = cv.resize(frame, (640, 480))
            if frame is None:
                print('--(!) No captured frame -- Break!')
                break
            self.detectAndDisplay(frame, face_cascade, body_cascade)
            # if cv.waitKey(10) == 27:
            if cv.waitKey(1) & 0xFF == ord('q'):
                break
            # if(time.time() - startTime > 5):
            #     print("5 SECONDS")
            #     startTime = time.time()
            #     for person in Person.potentialArray: 
            #         print(person)
            #     for person in Person.verifiedArray: 
            #         print(person)
        return Person.verifiedArray
    
    def detectAndDisplay(self, frame, face_cascade, body_cascade):
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
            # Add to person arrays
            self.addToArrays(x, y, w, h)
        # Update arrays
        self.updateArrays()
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
        cv.imshow('Capture - Face and body detection', frame)

    # Create people array
    # Criteria: 
    # Person if has been detected 90% of the time for > 3 seconds
    # Continues to be a person detected until
    # Not detected 90% of the time for 3 seconds
    # Distance: += 50 coordinates on both x and y
    # Given x, y, w, h
    def addToArrays(self, x, y, w, h):
        # Check if coordinates are already in verifiedPeople array
        alreadyVerified = False
        smallX = x - self.distance
        largeX = x + self.distance
        smallY = y - self.distance
        largeY = y + self.distance
        for person in Person.verifiedArray: 
            if(smallX < person.x < largeX and smallY < person.y < largeY): 
                alreadyVerified = True
                break
        # If already verified
        #   Update stats 
        # If not, check if coordinates are already in potentialPeople
        #   If already in, update stats
        #   If not, add them into potentialPeople(happens in declaration)
        if(alreadyVerified):
            for person in Person.verifiedArray: 
                if(smallX < person.x < largeX and smallY < person.y < largeY): 
                    person.updateStats(1)
                    break
        else:  
            alreadyPotential = False
            for person in Person.potentialArray: 
                if(smallX < person.x < largeX and smallY < person.y < largeY): 
                    alreadyPotential = True
                    person.updateStats(1)
                    break
            if not alreadyPotential: 
                potentialPerson = Person(x, y, w, h, time.time(), time.time(), True, 1, 1, 1)

            
    # Goes through potentialArray and verifiedArray to add any potentials into veriifed
    # and delete any non-person from potential and verified
    def updateArrays(self):
        # ADDING
        # Check if any people in potentialPeople should be in verifiedPeople
        # Not already verified, Time lived >= 3 seconds, and percentDetected >= 90% 
        # DELETING
        # Also check if any people in potentialPeople should be kicked
        # Not already verified, Time since last detection >= 3s, percentDetected < 90% 
        for person in Person.potentialArray: 
            # Make sure not already in verifiedPeople 
            if( not person.verified and time.time() - person.timeFirstDetected >= self.time and person.percentDetected >= self.percent):
                Person.verifiedArray.append(person)
                person.verified = True
                Person.potentialArray.remove(person)
            if(not person.verified and time.time() - person.timeLastDetected >= self.time and person.percentDetected < self.percent): 
                Person.potentialArray.remove(person)
        
        # Check if any verifiedPeople no longer belong in verified
        # Time since last detection >= 3s, percentDetected < 90%
        for person in Person.verifiedArray: 
            if(time.time() - person.timeLastDetected >= self.time and person.percentDetected < self.percent): 
                Person.verifiedArray.remove(person)
        
        # For all people, both in verified and potential
        # If not seenThisRound, then updateStats(-1) 
        # Set seenThisRound to False for ALL to reset
        for person in Person.verifiedArray: 
            if(not person.seenThisRound):
                person.updateStats(-1)
            person.seenThisRound = False
            




