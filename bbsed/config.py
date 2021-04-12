import os
import configparser


class Section:
    """
    Simple config section definition.
    """
    def __init__(self, save):
        self.data = {}
        self.save = save

    def __getitem__(self, setting):
        """
        Get setting value.
        """
        return self.data[setting]

    def __setitem__(self, setting, value):
        """
        Set setting value.
        """
        self.data[setting] = value


class Configuration:
    """
    Simple configuration base class.
    """

    SETTINGS = {}

    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.settings = {}

        # Initialize all settings with their default values.
        for section, settings in self.SETTINGS.items():
            self.settings[section] = Section(self.save)

            for setting, initial in settings.items():
                self.settings[section][setting] = initial

        self.load()

    def load(self):
        """
        Load config from disk if it exists.
        """
        if os.path.exists(self.cfg_path):
            parser = configparser.ConfigParser()

            with open(self.cfg_path, "r") as cfg_fp:
                parser.read_file(cfg_fp)

            for section, settings in self.SETTINGS.items():
                for setting, _ in settings.items():
                    self.settings[section][setting] = parser.get(section, setting)

    def save(self):
        """
        Save config to disk.
        """
        parser = configparser.ConfigParser()

        for section, settings in self.SETTINGS.items():
            parser.add_section(section)

            for setting in settings.keys():
                setting_value = self.settings[section][setting]
                parser.set(section, setting, setting_value)

        with open(self.cfg_path, "w") as cfg_fp:
            parser.write(cfg_fp)

    def __getitem__(self, section):
        """
        Get section object.
        """
        return self.settings[section]
