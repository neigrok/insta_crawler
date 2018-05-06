from settings import *

import re
import time
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import mkdir
from filehandler import FileHandler

class Crawler:
    def __init__(self, path=PATH, img_path=IMG_PATH, driver_path='\\chromedriver.exe', quality='320w'):
        self.path = path
        self.img_path = img_path
        # prepare folders for data
        mkdir(path)
        mkdir(img_path)

        # instantiate a chrome options object so you can set the size and headless preference
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1600x900")

        # download the chrome driver from https://sites.google.com/a/chromium.org/chromedriver/downloads
        #  and put it in the current directory
        chrome_driver = os.getcwd() + driver_path
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

        # store usernames
        self.users = set()
        self.visited_users = set()

        # file quality (resolution?)
        #  must be one of these:
        #   the worst -- 150w | 240w | 320w | 480w | 640w -- the best
        self.quality = quality

    def collect_pictures(self, quality):
        # collect data from page
        data = []
        for el in self.driver.find_elements_by_tag_name('img'):
            raw_text = el.get_attribute('alt')
            hashtags = re.findall(r'(#[а-яА-Яa-zA-Z0-9_]+ *)', raw_text)
            if len(hashtags):
                img = el.get_attribute('srcset')
                images = re.findall(r'(http.*? )(\d+w)', img)
                for image in images:
                    if image[1] == quality:
                        data.append((image[0], ''.join(hashtags)))
        return data

    def collect_comment_pages(self):
        # Those pages are used to check commentaries for new usernames
        a_tags = self.driver.find_elements_by_tag_name("a")
        hrefs = []
        for a in a_tags:
            href = a.get_attribute('href')
            if 'https://www.instagram.com/p/' in href:
                hrefs.append(href)
        return hrefs

    def extract_names(self, link):
        # Take usernames from comment page
        self.driver.get(link)
        comments = self.driver.find_elements_by_class_name('_2g7d5')  # не уверен в надежности

        names = []
        for comment in comments:
            name = comment.get_attribute('title')
            names.append(name)
        return names

    def getlink(self):
        # Get random user from users set and create link to his profile
        user = (self.users - self.visited_users).pop()
        self.visited_users.add(user)
        link = 'https://www.instagram.com/' + user
        return link, user

    def serialize(self):
        mkdir(SAVE_FILE)
        with open(os.path.join(SAVE_FILE, 'users.pickle'), 'wb') as handle:
            pickle.dump(self.users, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join(SAVE_FILE, 'visited_users.pickle'), 'wb') as handle:
            pickle.dump(self.visited_users, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def deserialize(self):
        with open(os.path.join(SAVE_FILE, 'users.pickle'), 'rb') as handle:
            self.users = pickle.load(handle)
        with open(os.path.join(SAVE_FILE, 'visited_users.pickle'), 'rb') as handle:
            self.visited_users = pickle.load(handle)

    def scroll_down(self, times=1):
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        i = 0
        while i < times:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            i += 1

    def scrap_users(self, username):
        self.users.add(username)
        self.run()

    def scrap_hashtag(self, hashtag):
        pass


    def run(self):
        # all file handling
        file = FileHandler(self.path, self.img_path)
        user = ''

        # entry point set
        if len(self.users) > 0:
            link, user = self.getlink()
        else:
            link = START_LINK

        while True:
            self.driver.get(link)

            # нужно доскролливать каждого пользователя до конца
            self.scroll_down(times=20)

            collected_data = self.collect_pictures(self.quality)
            try:
                file.write(collected_data, user=user)
            except Exception as e:
                print(e)
                self.serialize()
                break

            links = self.collect_comment_pages()
            for link in links:
                names = self.extract_names(link)
                self.users |= set(names)

            link, user = self.getlink()

    def __del__(self):
        # close chrome
        self.driver.close()
