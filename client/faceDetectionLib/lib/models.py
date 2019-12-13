import numpy as np
import cv2
import time
import os
import dlib

class FaceDetectorWrapper:
    def __init__(self):
        return
    def detect(self, cv2_img): 
        # should return a list of face coordinates
        return
    def detect_with_evaluation(self, cv2_img):
        start = time.time()
        faces = self.detect(cv2_img)
        end = time.time()

        print(f'Interval: {end-start:.2f}s - FPS: {1 / round(end-start, 2):.2f} - Detected: {len(faces)}')
        return faces

class HaarCascade(FaceDetectorWrapper):
    def __init__(self):
        super().__init__()
        self.face_cascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml'))

    def detect(self, cv2_img, scaleFactor=1.1, minNeighbors=5, minSize=(30,30)):
        gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=scaleFactor, minNeighbors=minNeighbors, minSize=minSize)

        return [(x, y, x+w, y+h) for (x, y, w, h) in faces]


class HoGDlib(FaceDetectorWrapper):
    def __init__(self):
        super().__init__()

        self.hogFaceDetector = dlib.get_frontal_face_detector()
    
    def detect(self, cv2_img):
        dlib_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        faces = self.hogFaceDetector(dlib_img, 0)

        return [(face.left(), face.top(), face.right(), face.bottom()) for face in faces]

class CNNDlib(FaceDetectorWrapper):
    def __init__(self):
        super().__init__()

        self.dnnFaceDetector = dlib.cnn_face_detection_model_v1(os.path.join(os.path.dirname(__file__), 'mmod_human_face_detector.dat'))
    
    def detect(self, cv2_img):
        dlib_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        faces = self.dnnFaceDetector(dlib_img, 0)

        return [(face.rect.left(), face.rect.top(), face.rect.right(), face.rect.bottom()) for face in faces]



    