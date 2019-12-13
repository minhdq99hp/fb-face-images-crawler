import numpy as np
import cv2
import sys, os
sys.path.append(os.path.realpath('..'))

from mtcnn.mtcnn import MTCNN
# pip install mtcnn
from lib.models import CNNDlib

faceDetector = MTCNN()

faceDetector = CNNDlib()

cap = cv2.VideoCapture('abb.mp4')

while(True):
    # Capture frame-by-frame
    ret, img = cap.read()

    h, w, = img.shape[0], img.shape[1]

    img = cv2.resize(img, (640, int(h / w * 640)))

    faces = faceDetector.detect(img)

    for (x1, y1, x2, y2) in faces:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # for mtcnn only
    # result = faceDetector.detect_faces(img)

    # for person in result:
    #     bounding_box = person['box']
    #     keypoints = person['keypoints']
        
    #     cv2.rectangle(img,
    #                 (bounding_box[0], bounding_box[1]),
    #                 (bounding_box[0]+bounding_box[2], bounding_box[1] + bounding_box[3]),
    #                 (0,155,255),
    #                 2)
    #     cv2.circle(img,(keypoints['left_eye']), 2, (0,155,255), 2)
    #     cv2.circle(img,(keypoints['right_eye']), 2, (0,155,255), 2)
    #     cv2.circle(img,(keypoints['nose']), 2, (0,155,255), 2)
    #     cv2.circle(img,(keypoints['mouth_left']), 2, (0,155,255), 2)
    #     cv2.circle(img,(keypoints['mouth_right']), 2, (0,155,255), 2)

    # # Our operations on the frame come here
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('frame', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()