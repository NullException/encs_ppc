import codecs
import json
from pprint import pprint

class SettingsProvider(object):
    def __init__(self, settings_path):
        with open(settings_path) as data_file:    
            self.data = json.load(data_file)
            print(self.data)

    def database_path(self):
        path = self.data['database']['path']
        print('database_path', path)
        return path

    def bot_secret_token(self):
        path = self.data['telegram_bot']['secret_token_path']
        f = open('secret_bot_token', 'r')
        token = f.readline()
        return token