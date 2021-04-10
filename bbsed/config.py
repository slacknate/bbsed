import os
import configparser


class Configuration:

    SETTINGS = {}

    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.load()

    def update(self, **kwargs):
        for setting_id, value in kwargs.items():
            section, setting = setting_id.split("_")

            if section not in self.SETTINGS:
                raise ValueError(f"Invalid setting name {setting}!")

            if setting not in self.SETTINGS[section]:
                raise ValueError(f"Invalid setting name {setting}!")

            setattr(self, setting_id, value)

        self.save()

    def load(self):
        parser = None

        if os.path.exists(self.cfg_path):
            parser = configparser.ConfigParser()

            with open(self.cfg_path, "r") as cfg_fp:
                parser.read_file(cfg_fp)

        for section, settings in self.SETTINGS.items():
            for setting, initial in settings.items():

                if parser is None:
                    setting_value = initial
                else:
                    setting_value = parser.get(section, setting)

                setattr(self, section + "_" + setting, setting_value)

    def save(self):
        parser = configparser.ConfigParser()

        for section, settings in self.SETTINGS.items():
            parser.add_section(section)

            for setting in settings.keys():
                setting_value = getattr(self, section + "_" + setting)
                parser.set(section, setting, setting_value)

        with open(self.cfg_path, "w") as cfg_fp:
            parser.write(cfg_fp)
