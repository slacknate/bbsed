import os
import platform

from .util import *
from .char_info import CHARACTER_INFO

BBCF_PATH_COMPONENTS = ("data", "Char")


def get_data_dir():
    """
    Get most top-level meta data directory for the app.
    If this directory does not exist we create it.
    """
    if platform.system().upper() == "WINDOWS":
        data_dir = os.path.join(os.environ["APPDATA"], "bbsed")

    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".bbsed")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return data_dir


def listdir_safe(full_path):
    """
    Helper to iterate a directory.
    The builtin `os.listdir()` raises an exception if the directory does not exist.
    Avoid that and return an empty list when we are given a path that does not exist.
    """
    dir_contents = []

    if os.path.exists(full_path):
        dir_contents = os.listdir(full_path)

    return dir_contents


class Paths:
    """
    Object to manage directories tracked within the app.
    Mostly exists so we have a consistent pathing across all our code
    and can change the paths to certain datas in one place rather than a billion.
    """
    def __init__(self):
        self.data_dir = get_data_dir()
        self.app_config = None

    def set_app_config(self, config):
        """
        Set reference to our AppConfig object.
        For use in the AppConfig constructor.
        """
        self.app_config = config

    @property
    def app_config_file(self):
        """
        Helper property to get the app config file path.
        """
        return os.path.join(self.data_dir, "app.conf")

    @property
    def select_config_file(self):
        """
        Helper property to get the selected palettes config file path.
        """
        return os.path.join(self.data_dir, "select.conf")

    @property
    def applied_config_file(self):
        """
        Helper property to get the applied palettes config file path.
        """
        return os.path.join(self.data_dir, "applied.conf")

    @property
    def steam_exe(self):
        """
        Helper property to get our steam.exe full path based on our configured Steam install location.
        """
        return os.path.join(self.app_config["bbsed"]["steam_install"], STEAM_PROCESS_NAME)

    @property
    def bbcf_data_dir(self):
        """
        Helper property to get our BBCF install location based on our configured Steam install location.
        """
        return os.path.join(self.app_config["bbsed"]["bbcf_install"], *BBCF_PATH_COMPONENTS)

    @staticmethod
    def _get_image_cache(cache_path):
        """
        Return a list of all HIP images for this character which are cached at `cache_path`.
        """
        image_cache = []

        for hip_image in listdir_safe(cache_path):
            hip_full_path = os.path.join(cache_path, hip_image)
            image_cache.append(hip_full_path)

        return image_cache

    def _get_sprite_cache_path(self, character):
        """
        Ensure all cached sprites the app manages are located in the same top-level directory.
        """
        return os.path.join(self.data_dir, "sprites", character)

    def get_sprite_cache_path(self, character):
        """
        Get the path where we should cache sprites for the given character.
        """
        return self._get_sprite_cache_path(character)

    def get_sprite_cache(self, character):
        """
        Return a list of all cached sprites for this character.
        """
        sprite_cache_path = self._get_sprite_cache_path(character)
        return self._get_image_cache(sprite_cache_path)

    def _get_collision_cache_path(self, character):
        """
        Ensure all cached collision box datas the app manages are located in the same top-level directory.
        """
        return os.path.join(self.data_dir, "collision_boxes", character)

    def get_collision_cache_path(self, character):
        """
        Get the path where we should cache collision box data for the given character.
        """
        return self._get_collision_cache_path(character)

    def _get_script_cache_path(self, character):
        """
        Ensure all cached script data the app manages are located in the same top-level directory.
        """
        return os.path.join(self.data_dir, "scripts", character)

    def get_script_cache_path(self, character):
        """
        Get the path where we should script data for the given character.
        """
        return self._get_script_cache_path(character)

    @staticmethod
    def _get_path_pcs(*pcs, specifier=None):
        """
        Get the path pieces of a save or edit path.
        Save and edit paths both conform to the following structure:

        - <top level>
            - <character>
                - <specifier>
                    - <specifier value>

        Note that a save path can have one further layer for the saved palette name.
        """
        if specifier is None:
            raise ValueError("Must provide a path specifier!")

        path_pcs = []

        # If we have at least one piece we were given a character.
        if len(pcs) >= 1:
            character = pcs[0]
            path_pcs.append(character)

        # If we have at least two pieces then we were also given a specifier and associated value.
        # This allows us to manage meta data directories for multiple different things.
        # The intent is for something like "pal" and a palette ID to be the specifier and associated value.
        if len(pcs) >= 2:
            specifier_value = pcs[1]
            path_pcs.append(specifier)
            path_pcs.append(specifier_value)

        # We will only get here for save paths.
        # If we have at least three pieces then we were given a palette save name.
        if len(pcs) >= 3:
            save_name = pcs[2]
            path_pcs.append(save_name)

        return path_pcs

    def _get_palette_edit_path(self, *pcs):
        """
        Ensure all the files the app can edit are located in the same top-level directory.
        For now we assume all edit paths are for palettes.
        """
        edit_path_pcs = self._get_path_pcs(*pcs, specifier="pal")
        return os.path.join(self.data_dir, "edit", *edit_path_pcs)

    def get_edit_palette_path(self, character, palette_id, slot_name):
        """
        Get the path of a characters palette cache subdirectory.
        """
        return self._get_palette_edit_path(character, palette_id, slot_name)

    def get_edit_lock_path(self, character, palette_id, slot_name):
        """
        Get the path of a palette lock file.
        """
        edit_path = self._get_palette_edit_path(character, palette_id, slot_name)
        return os.path.join(edit_path, LOCK_FILE_NAME)

    def get_edit_palette(self, character, palette_id, slot_name):
        """
        Get a list of HPL palette files in the given slot for the given character and palette ID.
        We specifically exclude any lock files found in this directory as we only care about palette files.
        """
        character_edit_path = self._get_palette_edit_path(character, palette_id, slot_name)
        edit_dir_listing = filter(lambda _hpl_file: _hpl_file != LOCK_FILE_NAME, listdir_safe(character_edit_path))
        return [os.path.join(character_edit_path, hpl_file) for hpl_file in edit_dir_listing]

    def walk_palette_edit(self, *characters, slot_name=None):
        """
        Iterate our top level cache directory.
        """
        if slot_name is None:
            raise ValueError("Must provide a slot name!")

        if not characters:
            characters = [character_id for _, character_id in CHARACTER_INFO.values()]

        for character in characters:
            for palette_id, _ in iter_palettes():
                hpl_files_list = self.get_edit_palette(character, palette_id, slot_name)

                if hpl_files_list:
                    yield character, palette_id, hpl_files_list

    def _get_palette_save_path(self, *pcs):
        """
        Ensure all the files the app separately saves as user data are located in the same top-level directory.
        For now we assume all save paths are for palettes.
        """
        save_path_pcs = self._get_path_pcs(*pcs, specifier="pal")
        return os.path.join(self.data_dir, "save", *save_path_pcs)

    def get_palette_save_path(self, character, palette_id, save_name):
        """
        Get the palette save path for a palette. A palette is associated to a character and palette ID.
        """
        return self._get_palette_save_path(character, palette_id, save_name)

    def get_palette_saves(self, character, palette_id):
        """
        Get a list of saved palettes for the given character and palette ID.
        """
        character_save_path = self._get_palette_save_path(character, palette_id)
        return listdir_safe(character_save_path)

    def get_saved_palette(self, character, palette_id, save_name):
        """
        Get a list of HPL palette files saved as `save_name` for the given character and palette ID.
        """
        character_save_path = self._get_palette_save_path(character, palette_id, save_name)
        return [os.path.join(character_save_path, hpl_file) for hpl_file in os.listdir(character_save_path)]

    def walk_palette_save(self, *characters):
        """
        Walk our top level palette save directory.
        """
        if not characters:
            characters = [character_id for _, character_id in CHARACTER_INFO.values()]

        for character in characters:
            for palette_id, palette_num in iter_palettes():
                for save_name in self.get_palette_saves(character, palette_id):
                    yield character, palette_id, save_name
