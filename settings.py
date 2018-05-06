import os

# path for saving index file and images
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# separate image folder
IMG_PATH = os.path.join(PATH, 'img')

# entry point
START_LINK = 'https://www.instagram.com/explore/tags/russia/'

# save file to stop scrapping and continue later
SAVE_FILE = os.path.join(PATH, 'dump')


SCROLL_PAUSE_TIME = 0.5