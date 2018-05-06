import os
import multiprocessing
import urllib.request


class FileHandler:
    def __init__(self, path, img_path):
        self.path = path
        self.img_path = img_path

    def write(self, data, user=''):
        with multiprocessing.Pool(5) as pool:
            pool.map(self.download, [(user, d) for d in data])

    def download(self, userdata):
        user, data = userdata
        link = data[0]
        filename = link.split('/')[-1].strip()
        hashtags = data[1].replace(' ', '')

        file = os.path.join(self.img_path, filename)

        urllib.request.urlretrieve(link, file)
        self.add_to_index(filename, hashtags, username=user)

    def add_to_index(self, filename, hashtags, username='', attempt=1):
        if attempt > 5:
            return
        try:
            with open(os.path.join(self.path, 'index.csv'), "a") as f:
                f.write(filename + ',' + username + ',' + hashtags + '\n')
        except PermissionError:
            self.add_to_index(filename, hashtags, attempt=attempt+1)
