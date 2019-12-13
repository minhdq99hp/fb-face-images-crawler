import cv2
import time
import subprocess
import requests


url = "http://127.0.0.1:3500/"
vid_name = ''
def video (seconds):
    cap = cv2.VideoCapture('rtsp://letan:abc~1234@10.32.60.214:554/Streaming/Channels/901')
    frameRate = cap.get(cv2.CAP_PROP_FPS)
    if(not cap.isOpened()):
        return "error"

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    name = "abc" + time.strftime("%d-%m-%Y_%X")+".avi"
    vid_name = name
    frame_width = int( cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height =int( cap.get( cv2.CAP_PROP_FRAME_HEIGHT))
    print(frameRate, frame_width, frame_height)
    out = cv2.VideoWriter(name, fourcc, frameRate, (int(cap.get(3)),int(cap.get(4))), 1)
    program_starts = time.time()
    result = subprocess.Popen(["ffprobe", name], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell=True)
    nFrames=0
    while(nFrames<seconds*frameRate):
        ret, frame = cap.read()
        # frame = cv2.resize(frame, (0,0), fx = 0.25, fy = 0.25)
        if ret==True:
            out.write(frame)
            nFrames += 1
        else:
            break
    cap.release()
    return name 
def send_file(name):
    mp3_f = open(name, 'rb')
    files = {'file': mp3_f}
    req = requests.post(url, files=files, json=data)
    print (req.status_code)
    print (req.content)
while(True):
    video(240)
    send_file(vid_name)
    print('done')
cv2.destroyAllWindows()
