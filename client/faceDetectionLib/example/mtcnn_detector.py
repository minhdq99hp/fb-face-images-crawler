import cv2
from mtcnn.mtcnn import MTCNN
# pip install mtcnn

faceDetector = MTCNN()

img = cv2.imread('tag2.jpg')
h, w = img.shape[0], img.shape[1]

result = faceDetector.detect_faces(img)

for person in result:
    bounding_box = person['box']
    keypoints = person['keypoints']
    
    cv2.rectangle(img,
                  (bounding_box[0], bounding_box[1]),
                  (bounding_box[0]+bounding_box[2], bounding_box[1] + bounding_box[3]),
                  (0,155,255),
                  2)
    cv2.circle(img,(keypoints['left_eye']), 2, (0,155,255), 2)
    cv2.circle(img,(keypoints['right_eye']), 2, (0,155,255), 2)
    cv2.circle(img,(keypoints['nose']), 2, (0,155,255), 2)
    cv2.circle(img,(keypoints['mouth_left']), 2, (0,155,255), 2)
    cv2.circle(img,(keypoints['mouth_right']), 2, (0,155,255), 2)

show = cv2.resize(img, (480, int(480 * h / w)))
cv2.imshow('MTCNN', show)
cv2.waitKey(0)
cv2.destroyAllWindows()
