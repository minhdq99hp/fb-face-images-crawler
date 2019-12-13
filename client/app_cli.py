from browser_crawler import FBCrawler
from random import shuffle
from lib.utils import read_json, get_undone_friendlist, get_undownloaded_friendlist
import os
import json
import sys

from tqdm import tqdm

def print_menu():
    print('\n------ MENU ------')
    print('1. Start crawling')
    print('2. Start filtering')
    print('3. Upload data')
    print('0. Exit')
    print('------------------')

if __name__ == '__main__':
    crawler = None

    # initialize crawler 
    crawler = FBCrawler(display_browser=True, fast_load=False, profile_name="crawler_profile")

    # load user data
    crawler.load_user_info_file()

    ans = -1
    while ans != 0:
        print_menu()
        try: 
            ans = int(input('Your choice ?: '))
        except ValueError:
            continue
        
        if ans == 1:
            if crawler.has_quited():
                crawler.init_browser()

            if len(crawler.user_info['friendlist']) == 0:
                crawler.crawl_friendlist()

            undownloaded_friendlist = get_undownloaded_friendlist(crawler.user_info['friendlist'])
            
            pbar = tqdm(total=len(crawler.user_info['friendlist']))

            for i in range(len(crawler.user_info['friendlist']) - len(undownloaded_friendlist)):
                pbar.update(1)

            for i in range(len(crawler.user_info['friendlist']) - len(undownloaded_friendlist), len(crawler.user_info['friendlist'])):
                pbar.write(f'LOG: Downloading {undownloaded_friendlist[i]}\'s images.')
                crawler.crawl_photos(undownloaded_friendlist[i], 'photos_of')
                crawler.crawl_photos(undownloaded_friendlist[i], 'photos_all')

                # write to metadata file
                metadata_path = os.path.join('data', undownloaded_friendlist[i], 'metadata.json')
                metadata = read_json(metadata_path)
                if 'state' in metadata:
                    if metadata['state'] not in ['done', 'downloaded']:
                        metadata['state'] = 'downloaded'
                else:
                    metadata['state'] = 'downloaded'

                with open(os.path.join('data', undownloaded_friendlist[i], 'metadata.json'), 'w', encoding='utf-8') as f:
                    f.write(json.dumps(metadata, indent=4))
                
                pbar.update(1)
        elif ans == 2:
            if len(crawler.user_info['friendlist']) == 0:
                crawler.crawl_friendlist()
            
            undone_friendlist = get_undone_friendlist(crawler.user_info['friendlist'])

            pbar = tqdm(total=len(crawler.user_info['friendlist']))

            for i in range(len(crawler.user_info['friendlist']) - len(undone_friendlist)):
                pbar.update(1)

            for i in range(len(crawler.user_info['friendlist']) - len(undone_friendlist), len(crawler.user_info['friendlist'])):
                pbar.write(f'LOG: Filtering {undone_friendlist[i]}\'s images.')
                crawler.filter(undone_friendlist[i])
                pbar.update(1)

        elif ans == 3:
            if len(crawler.user_info['friendlist']) == 0:
                crawler.crawl_friendlist()
            shuffle(crawler.user_info['friendlist'])

            pbar = tqdm(total=len(crawler.user_info['friendlist']))

            for i in range(len(crawler.user_info['friendlist'])):
                pbar.write(f'LOG: Uploading {crawler.user_info["friendlist"][i]}\'s images.')
                crawler.upload(crawler.user_info['friendlist'][i])

                
                pbar.update(1)

        elif ans == 0:
            print('EXIT PROGRAM')
            crawler.quit()
            break
    
    
