import cv2
import sys, os
sys.path.append(os.path.realpath('..'))

from lib.models import HaarCascade

img = cv2.imread('assets/example-03.jpg')

faceDetector = HaarCascade()

# faces = faceDetector.detect(img)
faces = faceDetector.detect_with_evaluation(img)

for (x1, y1, x2, y2) in faces:
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

show = cv2.resize(img, (1280, 720))
cv2.imshow('Haar-cascade', show)

# cv2.imwrite('output/example-03.jpg', img)

cv2.waitKey(0)
cv2.destroyAllWindows()