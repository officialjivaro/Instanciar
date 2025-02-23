# logic/config_handler.py
import os
import configparser

class ConfigHandler:
    def __init__(self):
        self.user_folder = os.path.expanduser("~")
        self.config_folder = os.path.join(self.user_folder, "Jivaro", "Instanciar", "config")
        self.settings_file = os.path.join(self.config_folder, "settings.ini")
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
        if not os.path.exists(self.settings_file):
            f = open(self.settings_file, "w")
            f.close()
        self.config = configparser.ConfigParser()
        self.config.read(self.settings_file)
