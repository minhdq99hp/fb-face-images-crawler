from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
import random
from bs4 import BeautifulSoup
from lib import utils
import time
import os
import sys
import zipfile
import json
import re
import requests
import urllib.request
import datetime
import queue
import cv2
import numpy as np
from random import shuffle
from lib.filter import *
from lib.utils import *

import face_recognition

from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler

class BrowserCrawler:
    # Function: this class use Firefox browser to fetch all rendered html of a page
    _driver = None
    _has_error = False
    _quited = False
    _diplay = None

    def __init__(self, timeout=60, display_browser=False, fast_load=True, profile_name=None):
        '''
        input
        -----

        timeout: timeout to load page
        display_browser: not run browser in headless mode
        fast_load: use ads block plugins, turn off css to load page faster
        profile (str): provide a profile name. Need to set up profile first
        '''
        # Create a headless Firefox browser to crawl

        self.options = Options()
        if display_browser == False:
            self.options.add_argument("--headless")

        if profile_name is None or profile_name == "":
            self.profile = webdriver.FirefoxProfile()
        else:
            self.profile = utils.get_firefox_profile(profile_name)
            print("Firefox profile: %s" % profile_name)

        if fast_load == True:

            self.profile.set_preference('permissions.default.stylesheet', 2)
            # Disable images
            self.profile.set_preference('permissions.default.image', 2)
            # Disable notification
            self.profile.set_preference(
                'permissions.default.desktop-notification', 2)
            # Disable Flash
            self.profile.set_preference(
                'dom.ipc.plugins.enabled.libflashplayer.so', 'false')
            # Adblock Extension
            self.profile.exp = "lib/adblock.xpi"
            self.profile.add_extension(extension=self.profile.exp)

        # self._driver = webdriver.Firefox(
        #     firefox_options=options, firefox_profile=profile)

        # Create a virtual screen to with Raspberry too
        # self._display = Display(visible=0, size=(1024,768))
        # self._display.start()
        # self._driver = webdriver.Firefox()

        self.timeout = timeout

        # self._driver.set_page_load_timeout(timeout)
        # self._quited = False
        self._quited = True
    
    def init_browser(self):
        self._driver = webdriver.Firefox(firefox_options=self.options, firefox_profile=self.profile)
        self._driver.set_page_load_timeout(self.timeout)
        self._quited = False

    def load_page(self, url, wait=5, entropy=3):
        # Function: load page with url
        # Input:
        # - wait: time waiting for page to load
        # - entropy: small random add to waiting time

        wait = int(wait + random.random() * entropy)
        # self._driver.set_page_load_timeout(wait) # Set timeout frequently may raise errors
        # self._driver.implicitly_wait(wait)

        self._has_error = False
        # a = True
        # while a:
        try:
            self._driver.get(url)
            a = False
            return True
        except Exception:
            print("Timeout")
            self._has_error = True
            return False

    def get_title(self):
        # Function: return page title
        return self._driver.title

    def get_page_html(self):
        # Return all html of an web
        return self._driver.page_source

    def has_error(self):
        return self._has_error

    def has_quited(self):
        return self._quited

    def quit(self):
        if self._quited == False:
            self._driver.quit()
            self._quited = True

class FBCrawler(BrowserCrawler):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        config = read_json('config.json')
        if config is not None:
            self.DATA_PATH = config['data-path']
            self.SERVER_URL = config['server-url']
            self.TEMP_PATH = config['temp-path']
        else:
            raise("Can't read config.json")

        self.FORCE_CRAWL = True
        self.SCROLL_PAUSE_TIME = 10
        self.SCROLL_TIME_OUT = 600
        self.SCROLL_MAX_ATTEMPT = 60
        self.MAX_IMAGE_PER_ID = 500

        self.user_info = None

        # self.detector = MTCNN()

    def load_user_info_file(self):
        with open('user_info.json', 'r+', encoding='utf-8') as f:
            self.user_info = json.load(f)

        if 'id' not in self.user_info or 'name' not in self.user_info:
            self.load_page("https://www.facebook.com")
            self.user_info['id'] = get_user_id_from_home_page(self._driver)
            self.user_info['name'] = get_user_name_from_home_page(self._driver, self.user_info['id'])
        else:
            self.user_info['id'], self.user_info['name'] = self.user_info['id'].rstrip(), self.user_info['name'].rstrip()
        
        if 'friendlist' not in self.user_info:
            self.user_info['friendlist'] = []
        else:
            self.user_info['friendlist'] = remove_redundant_id(self.user_info['friendlist'])
        

        # if 'friendlist-update-datetime' not in self.user_info:
        #     self.user_info['friendlist-update-datetime'] = ''
        
        # SAVE BACK TO FILE
        with open('user_info.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.user_info, indent=4))

    def scroll_until_exists(self, elem_ids, time_out=None):
        if time_out is None:
            time_out = 240 # seconds

        start = time.time()

        while True:
            actions = ActionChains(self._driver)
            actions.send_keys(Keys.PAGE_DOWN)
            actions.perform()

            time.sleep(0.5)

            # exit condition
            found = False
            for elem_id in elem_ids:
                try:
                    self._driver.find_element_by_id(elem_id)
                    found = True
                    break
                except Exception:
                    continue

            if found == True:
                break

            # check time out
            if time.time() - start >= time_out:
                break

    def crawl_friendlist(self):
        '''
        Step 1: Go into friends page. Scroll until all the friends are shown up.
        Step 2: Get the friends id.
        Step 3: Save back to the user_info.json 
        '''

        self.load_page(f"https://www.facebook.com/{self.user_info['id']}/friends")

        self.scroll_until_exists(['pagelet_timeline_medley_movies', 'pagelet_timeline_medley_books', 
                                'pagelet_timeline_medley_music', 'pagelet_timeline_medley_photos', 
                                'pagelet_timeline_medley_videos', 'pagelet_timeline_medley_map', 
                                'pagelet_timeline_medley_likes', 'pagelet_timeline_medley_review', 
                                'pagelet_timeline_medley_app_instapp'])

        id_list = [self.user_info['id']]

        # read page source to get friend's id.
        soup = BeautifulSoup(self._driver.page_source, 'html5lib')
        for d in soup.find_all("div", class_="fsl fwb fcb"):
            try:
                link = list(d.children)[0]['data-gt']
                data_link = json.loads(link)
                id_list.append(data_link['engagement']['eng_tid'].rstrip())
            except KeyError:
                continue

        self.user_info['friendlist'] = remove_redundant_id(id_list)

        with open('user_info.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.user_info, indent=4))

    def crawl_photos(self, fbid, section):
        '''
        Step 1: Check state in metadata. If state is 'done' or 'downloaded', then stop.
        Step 2: Go to photos section. Scroll until all photos are shown up.
        '''
        data_path = os.path.join(os.path.dirname(__file__), 'data', fbid)
        touch_dir(data_path)

        metadata = read_json(os.path.join(data_path, 'metadata.json'))

        if metadata is not None:
            if 'state' in metadata:
                if metadata['state'] in ['downloaded', 'done']:
                    # this id is downloaded or done.
                    return
        else:
            metadata = {}
            metadata['id'] = fbid


        # Start Crawling
        img_list = set(img.strip('.jpg') for img in os.listdir(data_path))
      
        tmp_queue = queue.Queue(maxsize=len(img_list))

        self.load_page(f"https://www.facebook.com/{fbid}/{section}")
        self.scroll_until_exists(['pagelet_timeline_medley_movies', 'pagelet_timeline_medley_books', 
                                'pagelet_timeline_medley_music', 
                                'pagelet_timeline_medley_videos', 'pagelet_timeline_medley_map', 
                                'pagelet_timeline_medley_likes', 'pagelet_timeline_medley_review', 
                                'pagelet_timeline_medley_app_instapp'])

        # get name
        name = self._driver.find_element_by_xpath("//input[@class='_1frb']").get_attribute('value')
        metadata['name'] = name

        wait = WebDriverWait(self._driver, 20)
        imageElements = self._driver.find_elements_by_xpath("//a[@class='uiMediaThumb _6i9 uiMediaThumbMedium']")
        # get image's id, aria-label, src, download img and relevant tags.
        last_src = ''
        for imageElement in imageElements:
            photo_id = imageElement.get_attribute('id').strip('pic_')
            aria_label = imageElement.get_attribute('aria-label')
            
            # skip if already downloaded
            if photo_id in img_list:
                continue

            # filter
            if not aria_label_filter(aria_label, name):
                continue

            # TODO: improve this code to make it run faster.
            self._driver.execute_script("arguments[0].click();", imageElement)

            time.sleep(2)
            try:
                attempt = 0
                img_src = ''
                while True:
                    elm_img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img.spotlight')))

                    img_src = elm_img.get_attribute('src')

                    if 'p206x206' in img_src: # low resolution img, not finish rendering -> wait for at most 3s.
                        if attempt < 3:
                            attempt += 1
                            time.sleep(1)
                            continue
                        else:
                            break 
                    else:
                        attempt = 0
                        break

                if attempt == 0: # high resolution img
                    # check if imageElement can't be clicked anymore. From now on, only raise exception.
                    if img_src == last_src:
                        raise('imageElement can\'t be clicked !')
                    else:
                        last_src = img_src

                    img_list.add(photo_id)

                    # Download image
                    img_path = f'data/{fbid}/{photo_id}.jpg'
                    urllib.request.urlretrieve(img_src, img_path)

                    # Process tag
                    img = cv2.imread(img_path)
                    h, w = img.shape[0], img.shape[1]

                    tagElements = self._driver.find_elements_by_xpath("//a[@class='_28r- photoTagLink']")

                    for tagElement in tagElements:
                        # get ID of tagged person
                        tag_id = tagElement.get_attribute('href').split('?id=')[1].rstrip()
                        # tag_name = tagElement.get_attribute('aria-label')

                        # get div of tag
                        bboxElement = tagElement.find_element_by_xpath(".//div[@class='fbPhotosPhotoTagboxBase tagBox']")
                        style = bboxElement.get_attribute('style')

                        x1, y1, x2, y2 = get_bbox_from_tag(style, h, w)

                        tag_img = img[y1:y2, x1:x2]

                        tag_folder_path = os.path.join('data', tag_id)
                        touch_dir(tag_folder_path)

                        tag_path = os.path.join(tag_folder_path, photo_id + '_tag.jpg')
                        if not os.path.exists(tag_path):
                            cv2.imwrite(tag_path, tag_img)
                        
                        img_list.add(photo_id + '_tag')                                                       

                    # Check if satisfy
                    if len(img_list) >= self.MAX_IMAGE_PER_ID:
                        # open(os.path.join(data_path, 'done'), 'w+').close()
                        break

                else:
                    # print("Put 1 image to queue because of time out.")
                    tmp_queue.put(imageElement)
                    continue # skip this img - should not happen

            except Exception as e:
                # raise
                print(e)
                continue
        
        # continue to process remain images
        # print(f'---REMAIN {tmp_queue.qsize()} IMAGES---')

        last_src = ''
        while not tmp_queue.empty():
            imageElement = tmp_queue.get()

            photo_id = imageElement.get_attribute('id').strip('pic_')
            aria_label = imageElement.get_attribute('aria-label')

            self._driver.execute_script("arguments[0].click();", imageElement)
            time.sleep(2)
            try:
                attempt = 0
                img_src = ''
                while True:
                    elm_img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img.spotlight')))
                    img_src = elm_img.get_attribute('src')
                    if 'p206x206' in img_src: # low resolution img, not finish rendering
                        if attempt < 3:
                            attempt += 1
                            time.sleep(1)
                            continue
                        else:
                            break 
                    else:
                        attempt = 0
                        break

                if attempt == 0: # high resolution img
                    # check if imageElement can't be clicked anymore. From now on, only raise exception.
                    if img_src == last_src:
                        raise('imageElement can\'t be clicked !')
                    else:
                        last_src = img_src

                    img_list.add(photo_id)

                    # Download image
                    urllib.request.urlretrieve(img_src, f'data/{fbid}/{photo_id}.jpg')

                    img = cv2.imread(img_path)
                    h, w = img.shape[0], img.shape[1]

                    tagElements = self._driver.find_elements_by_xpath("//a[@class='_28r- photoTagLink']")

                    for tagElement in tagElements:
                        # get ID of tagged person
                        tag_id = tagElement.get_attribute('href').split('?id=')[1].rstrip()
                        # tag_name = tagElement.get_attribute('aria-label')

                        # get div of tag
                        bboxElement = tagElement.find_element_by_xpath(".//div[@class='fbPhotosPhotoTagboxBase tagBox']")
                        style = bboxElement.get_attribute('style')

                        x1, y1, x2, y2 = get_bbox_from_tag(style, h, w)

                        tag_img = img[y1:y2, x1:x2]

                        tag_folder_path = os.path.join('data', tag_id)
                        touch_dir(tag_folder_path)

                        tag_path = os.path.join(tag_folder_path, photo_id + '_tag.jpg')
                        if not os.path.exists(tag_path):
                            cv2.imwrite(tag_path, tag_img)
                        
                        img_list.add(photo_id + '_tag')      

                    # Check if satisfy
                    if len(img_list) >= self.MAX_IMAGE_PER_ID:
                        # open(os.path.join(data_path, 'done'), 'w+').close()
                        break

                else:
                    # print("Skip 1 image because of time out.")
                    # tmp_queue.put(imageElement)
                    continue # skip this img - should not happen

            except Exception as e:
                # print('Skip 1 image because of error')
                continue

        # write to metadata file
        if not os.path.exists(os.path.join(data_path, 'metadata.json')):
            with open(os.path.join(data_path, 'metadata.json'), 'w', encoding='utf-8') as f:
                f.write(json.dumps(metadata, indent=4))

    def filter(self, fbid):
        '''
        Step 1: Check metadata if this fbid is filtered
        Step 2: Filter the tag ones
        '''
        
        data_path = os.path.join(self.DATA_PATH, fbid)
        metadata = read_json(os.path.join(data_path, 'metadata.json'))

        if metadata is not None:
            if 'state' in metadata:
                if metadata['state'] != 'downloaded':
                    return
        else:
            return
       
        filter_path = os.path.join(data_path, 'filter')
        touch_dir(filter_path)
        os.system(f"rm -rf {filter_path}/*")


        tag_list, origin_list = [], []

        for img_name in os.listdir(data_path):
            if img_name.endswith('_tag.jpg'):
                tag_list.append(img_name)
            elif img_name.endswith('.jpg'):
                origin_list.append(img_name)
        
        if len(tag_list) > 30:
            encoding_dict = {}
            for tag_img in tag_list:
                img_path = os.path.join(data_path, tag_img)
                
                img = cv2.imread(img_path)
                faces, bboxes = get_faces_and_bboxes(img_path)

                if len(faces) == 1:
                    encoding_dict[tag_img] = [faces[0], face_recognition.face_encodings(cv2.cvtColor(faces[0], cv2.COLOR_BGR2RGB), known_face_locations=[(0, 0, faces[0].shape[1], faces[0].shape[0])])[0]]

            # Filter with DBSCAN
            X = [encoding_dict[k][1] for k in encoding_dict.keys()]
            # Compute DBSCAN
            db = DBSCAN(eps=0.45, min_samples=10).fit(X)
            labels = db.labels_

            # Number of clusters in labels, ignoring noise if present.
            n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise_ = list(labels).count(-1)

            # Remove noise data points
            for i in range(len(labels)):
                if labels[i] == -1:
                    removed_keys = []
                    for k in encoding_dict.keys():
                        if np.array_equal(encoding_dict[k][1], X[i]):
                            removed_keys.append(k)
                    
                    for k in removed_keys:
                        del encoding_dict[k]
                        # print(f'remove noise {k}')

            # Write to filter_path
            for k in encoding_dict.keys():
                cv2.imwrite(os.path.join(filter_path, k), encoding_dict[k][0])

            # Get center 
            center_encoding = 0
            for k in encoding_dict.keys():
                center_encoding += encoding_dict[k][1]
            center_encoding = center_encoding / len(encoding_dict.keys())

            for img_name in origin_list:
                img_path = os.path.join(data_path, img_name)
                faces, bboxes = get_faces_and_bboxes(img_path)

                for i in range(len(faces)):
                    encoding = face_recognition.face_encodings(cv2.cvtColor(faces[i], cv2.COLOR_BGR2RGB), known_face_locations=[(0, 0, faces[i].shape[1], faces[i].shape[0])])[0]
                    
                    if face_recognition.compare_faces([encoding], center_encoding, tolerance=0.275)[0] == True:
                        # print('YES ' + img_name.replace('.jpg', f'_{i}.jpg'))
                        cv2.imwrite(os.path.join(filter_path, img_name.replace('.jpg', f'_{i}.jpg')), faces[i])
        else:
            # tag image is not reliable so use DBSCAN to get the largest cluster
            encoding_dict = {}
            for img_name in tag_list + origin_list:
                img_path = os.path.join(data_path, img_name)

                img = cv2.imread(img_path)

                faces, bboxes = get_faces_and_bboxes(img_path)

                if len(faces) == 1:
                    encoding_dict[img_name] = [faces[0], face_recognition.face_encodings(cv2.cvtColor(faces[0], cv2.COLOR_BGR2RGB), known_face_locations=[(0, 0, faces[0].shape[1], faces[0].shape[0])])]
                elif len(faces) > 1:
                    for i in range(len(faces)):
                        encoding_dict[img_name.replace('.jpg', f'_{i}.jpg')] = [faces[0], face_recognition.face_encodings(cv2.cvtColor(faces[i], cv2.COLOR_BGR2RGB), known_face_locations=[(0, 0, faces[i].shape[1], faces[i].shape[0])])[0]]

            
            X = [encoding_dict[k][1] for k in encoding_dict.keys()]

            # Compute DBSCAN
            db = DBSCAN(eps=0.45, min_samples=10).fit(X)
            labels = db.labels_

            n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise_ = list(labels).count(-1)

            largest_cluster_label = most_frequent(labels)

            for i in range(len(labels)):
                if labels[i] == largest_cluster_label:
                    for k in encoding_dict.keys():
                        if np.array_equal(encoding_dict[k][1], X[i]):
                            cv2.imwrite(os.path.join(filter_path, k), encoding_dict[k][0])
                            break
        
        # write to metadata file
        metadata['state'] = 'done'

        with open(os.path.join(data_path, 'metadata.json'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(metadata, indent=4))
    
    def upload(self, fbid):
        data_path = os.path.join(self.DATA_PATH, fbid)
        metadata = read_json(os.path.join(data_path, 'metadata.json'))

        if metadata is not None:
            if 'state' in metadata:
                if metadata['state'] != 'done':
                    print(f'--- SKIP {fbid} ---')
                    return
        else:
            print(f'--- SKIP {fbid} ---')
            return

        # compress fbid folder to zip file
        zipfile_path = os.path.join(self.TEMP_PATH, f'{fbid}.zip')
        fbid_path = os.path.join(self.DATA_PATH, fbid)

        if not os.path.exists(fbid_path):
            raise FileNotFoundError

        zipf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)

        cwd = os.getcwd()
        os.chdir(self.DATA_PATH)
        zipdir(fbid, zipf)
        zipf.close()

        os.chdir(cwd)

        files = {
            'data': open(zipfile_path, 'rb')
        }

        try:
            response = requests.post(self.SERVER_URL + 'upload-data', files=files)
        except Exception as e:
            print(e)