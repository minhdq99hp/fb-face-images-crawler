import cv2

def draw_bbox(cv2_img, bboxes):
    for (x1, y1, x2, y2) in bboxes:
        cv2.rectangle(cv2_img, (x1, y1), (x2, y2), (0, 255, 0), 2)