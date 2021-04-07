import os
import configparser

SETTINGS = ("steam_install",)


class Configuration:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.steam_install = ""
        self.load()

    def update(self, **kwargs):
        for setting, value in kwargs.items():
            if setting not in SETTINGS:
                raise ValueError(f"Invalid setting name {setting}!")

            setattr(self, setting, value)

        self.save()

    def load(self):
        if os.path.exists(self.cfg_path):
            parser = configparser.ConfigParser()

            with open(self.cfg_path, "r") as cfg_fp:
                parser.read_file(cfg_fp)

            self.steam_install = parser.get("bbsed", "steam_install")

    def save(self):
        parser = configparser.ConfigParser()

        parser.add_section("bbsed")
        parser.set("bbsed", "steam_install", self.steam_install)

        with open(self.cfg_path, "w") as cfg_fp:
            parser.write(cfg_fp)
