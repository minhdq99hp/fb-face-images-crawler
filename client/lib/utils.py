import os
# import sys

import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
import requests 
import json
import cv2

def read_json(file_path):
    try:
        json_file = open(file_path, 'r')
        data = json.load(json_file)

        # string preprocess
        for k in data.keys():
            if isinstance(data[k], str):
                data[k] = data[k].strip()

        json_file.close()
        return data
    except FileNotFoundError:
        return None

config = read_json('config.json')

if config is None:
    raise("config.json is not found.")

from mtcnn.mtcnn import MTCNN
face_detector = MTCNN()
os.system('clear')

# def scroll_until_max_height(self, elem_id, time_out=None, max_attempt=None):
#     if time_out is None:
#         time_out = self.SCROLL_TIME_OUT
    
#     if max_attempt is None:
#         max_attempt = self.SCROLL_MAX_ATTEMPT

#      # Scroll downward until the friend list is fully loaded.
#     friend_list = self._driver.find_element_by_id(elem_id)
#     threshold_size = friend_list.size
#     attempt = 0

#     while True:
#         actions = ActionChains(self._driver)
#         actions.send_keys(Keys.PAGE_DOWN)
#         actions.perform()

#         # self._driver.implicitly_wait(50)
#         time.sleep(0.5)
#         new_size = friend_list.size

#         # print(new_size)

#         if new_size['height'] == threshold_size['height']:
#             attempt += 1
#         else:
#             attempt = 0
#             threshold_size = new_size

#         if attempt == max_attempt:
#             break


def get_independent_os_path(path_list):
    path = ""
    for item in path_list:
        path = os.path.join(path, item)
    return path

def get_firefox_profile(profile_name):
    '''
    function: return profile if exists, else create new
    input
    -----
    profile_name (str): profile in name
    '''

    # print(profile_name)

    profile_path = get_independent_os_path(['lib', 'profiles', profile_name])
    
    if os.path.isdir(profile_path):
        return webdriver.FirefoxProfile(profile_path)
    else:
        print("profile %s doesn't exist yet") 
        print("i will create profile path at %s" % profile_path)
        print("then you need to create %s profile with setup_browser.py")
        print("you default profile in this session") 
        os.mkdir(profile_path)
        return None

def get_user_id_from_home_page(driver):
    avatar_img = driver.find_element_by_xpath('//img[@class="_2qgu _7ql _1m6h img"]')
    user_id = avatar_img.get_attribute("id").strip("profile_pic_header_").rstrip()
    return user_id

def get_user_name_from_home_page(driver, user_id):
    title_element = driver.find_element_by_xpath(f"//li[@data-nav-item-id=\"{user_id}\"]/a")
    user_name = title_element.get_attribute("title").rstrip()
    return user_name

def scroll_until_max_height(self, elem_id, time_out=None, max_attempt=None):
    if time_out is None:
        time_out = self.SCROLL_TIME_OUT
    
    if max_attempt is None:
        max_attempt = self.SCROLL_MAX_ATTEMPT
    
    # Scroll downward until the friend list is fully loaded.
    friend_list = self._driver.find_element_by_id(elem_id)
    threshold_size = friend_list.size
    attempt = 0

    while True:
        actions = ActionChains(self._driver)
        actions.send_keys(Keys.PAGE_DOWN)
        actions.perform()

        # self._driver.implicitly_wait(50)
        time.sleep(0.5)
        new_size = friend_list.size

        # print(new_size)

        if new_size['height'] == threshold_size['height']:
            attempt += 1
        else:
            attempt = 0
            threshold_size = new_size

        if attempt == max_attempt:
            break

def touch_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def get_bbox_from_tag(text, height, width):
    bbox = [x for x in text.split(';')]
    bbox = [float(x.split(':')[1][:-1]) for x in bbox[:len(bbox)-1]]

    x1 = int(width * bbox[2] / 100)
    y1 = int(height * bbox[3] / 100)
    x2 = int(x1 + width * bbox[0] / 100)
    y2 = int(y1 + height * bbox[1] / 100)

    return (x1, y1, x2, y2)

def remove_redundant_id(friendlist):
    try:
        response = requests.post(config['server-url'] + 'get-filtered-friendlist', json={"friendlist": friendlist})
        return response.json()['friendlist']
    except requests.exceptions.ConnectionError:
        print("Can't get filtered friendlist. Connection is refused.")
        return friendlist

def get_undownloaded_friendlist(friendlist):
    '''
    Get all friends that aren't downloaded
    '''
    undownloaded_friendlist = []
    for friend in friendlist:
        metadata_path = os.path.join(config['data-path'], friend, 'metadata.json')
        if os.path.exists(metadata_path):
            metadata = read_json(metadata_path)
            if 'state' not in metadata:
                undownloaded_friendlist.append(friend)
            else:
                if metadata['state'] not in ['done', 'downloaded']:
                    undownloaded_friendlist.append(friend)

        else:
            undownloaded_friendlist.append(friend)
        
    return undownloaded_friendlist

def get_undone_friendlist(friendlist):
    '''
    Get all friends with state 'downloaded'
    '''
    undone_friendlist = []
    for friend in friendlist:
        metadata_path = os.path.join(config['data-path'], friend, 'metadata.json')
        if os.path.exists(metadata_path):
            metadata = read_json(metadata_path)
            if metadata['state'] == 'downloaded':
                undone_friendlist.append(friend)

def get_faces_and_bboxes(img_path):
    margin = 32
    min_width = 30
    min_height = 30
    min_confidence = 0.5
    input_image_size = 160

    img = cv2.imread(img_path)
    h, w, c = img.shape

    result = face_detector.detect_faces(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    faces = []
    bboxes = []

    for res in result:

        if res['confidence'] < min_confidence or res['box'][2] < min_width or res['box'][3] < min_height:
            continue
        
        (x1, y1, x2, y2) = (res['box'][0], res['box'][1], res['box'][0] + res['box'][2], res['box'][1] + res['box'][3])
        
        # add margin
        x1 = max(int(x1 - margin/2), 0)
        y1 = max(int(y1 - margin/2), 0)
        x2 = min(int(x2 + margin/2), w)
        y2 = min(int(y2 + margin/2), h)

        resized_img = cv2.resize(img[y1:y2, x1:x2].copy(), (input_image_size, input_image_size))
        if resized_img is not None:
            faces.append(resized_img)

        bboxes.append((x1, y1, x2, y2))
    return faces, bboxes

def most_frequent(List):
    counter = 0
    num = List[0]
      
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i
  
    return num

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))