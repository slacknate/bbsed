import os
import platform

BBCF_PATH_COMPONENTS = ("steamapps", "common", "BlazBlue Centralfiction", "data", "Char")


def get_data_dir():
    if platform.system().upper() == "WINDOWS":
        data_dir = os.path.join(os.environ["APPDATA"], "bbsed")

    else:
        data_dir = os.path.join(os.path.expanduser("~"), "bbsed")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return data_dir


class Paths:
    """
    Object to manage directories tracked within the app.
    Mostly exists so we have a consistent pathing across all our code
    and can change the paths to certain datas in one place rather than a billion.
    """
    def __init__(self):
        self.data_dir = get_data_dir()
        self.config = None

    def set_config(self, config):
        """
        Set reference to our Configuration object.
        For use in the Configuration constructor.
        """
        self.config = config

    @property
    def app_config(self):
        """
        Helper property to get the app config file path.
        """
        return os.path.join(self.data_dir, "app.conf")

    @property
    def steam_exe(self):
        """
        Helper property to get our steam.exe full path based on our configured Steam install location.
        """
        return os.path.join(self.config.steam_install, "steam.exe")

    @property
    def bbcf_data_dir(self):
        """
        Helper property to get our BBCF install location based on our configured Steam install location.
        """
        return os.path.join(self.config.steam_install, *BBCF_PATH_COMPONENTS)

    def get_character_cache_path(self, abbreviation):
        """
        Get the path of a characters cache directory.
        """
        return os.path.join(self.data_dir, abbreviation)

    def get_image_cache_path(self, abbreviation):
        """
        Get the path of a characters image cache subdirectory.
        """
        return os.path.join(self.data_dir, abbreviation, "img")

    def get_palette_cache_path(self, abbreviation):
        """
        Get the path of a characters palette cache subdirectory.
        """
        return os.path.join(self.data_dir, abbreviation, "pal")

    def iter_data_dir(self):
        """
        Iterate our top level cache directory.
        """
        for character in os.listdir(self.data_dir):
            # The app config file lives in this directory, we should ignore it.
            if character not in ("app.conf",):
                yield character
