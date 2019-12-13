import cv2
import sys, os
sys.path.append(os.path.realpath('..'))

from lib.models import CNNDlib

img = cv2.imread('assets/example-03.jpg')

faceDetector = CNNDlib()

faces = faceDetector.detect_with_evaluation(img)

for (x1, y1, x2, y2) in faces:
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

cv2.imshow('CNN based Dlib', img)

# cv2.imwrite('output/example-03.jpg', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
