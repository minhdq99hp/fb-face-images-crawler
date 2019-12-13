# face-detection-lib
This repository contains several face detection algorithms. I'm using wrapper for all models to make those easier to implement.

```
class FaceDetectorWrapper:
    def __init__()
    def detect()
    def detect_with_evaluation
```

## Haar Cascade
## HoG Based Dlib
## CNN Based Dlib

The Pros and Cons of those algorithms are [here](https://www.learnopencv.com/face-detection-opencv-dlib-and-deep-learning-c-python/)

## Comparision
Example: ![Example](example/output/example-03.jpg)
Ground Truth: 8 faces
### On CPU
|Models        |FPS |Result  |
|--------------|----|--------|
|HaarCascade   |0.75|11 faces|
|HoG Based Dlib|2.17|8  faces|
|CNN Based Dlib|0.11|9  faces|

### On GPU
