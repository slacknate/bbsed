import os
import configparser


class ConfigCopy:
    """
    Object to wrap a copy of a Configuration that is iterable in the same way.
    """
    def __init__(self, settings):
        self.settings = settings

    def __getitem__(self, section):
        """
        Get section.
        """
        return self.settings[section]

    def __iter__(self):
        """
        Yield the same tuple that a real Configuration does.
        """
        for section, settings in self.settings.items():
            for setting, value in settings.items():
                yield section, setting, value


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
            self.settings[section] = {}

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

    def copy(self):
        """
        Return a copy of the settings dict.
        """
        settings_copy = {}

        for section, settings in self.settings.items():
            settings_copy[section] = {}

            for setting, value in settings.items():
                settings_copy[section][setting] = value

        return ConfigCopy(settings_copy)

    def __getitem__(self, section):
        """
        Get section.
        """
        return self.settings[section]

    def __iter__(self):
        """
        Iterate all settings in the config.
        """
        for section, settings in self.settings.items():
            for setting, value in settings.items():
                yield section, setting, value
