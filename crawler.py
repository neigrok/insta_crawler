from settings import *

import re
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
        # Get random user from users and create link to his profile
        user = (self.users - self.visited_users).pop()
        self.visited_users.add(user)
        link = 'https://www.instagram.com/' + user
        return link

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

    def run(self):
        # all file handling
        file = FileHandler(self.path, self.img_path)

        # entry point set
        if len(self.users) > 0:
            link = self.getlink()
        else:
            link = START_LINK

        while True:
            self.driver.get(link)
            collected_data = self.collect_pictures(self.quality)
            file.write(collected_data)

            if len(self.users - self.visited_users) < 100:
                links = self.collect_comment_pages()
                for link in links:
                    names = self.extract_names(link)
                    self.users |= set(names)

            link = self.getlink()

    def __del__(self):
        # close chrome
        self.driver.close()
