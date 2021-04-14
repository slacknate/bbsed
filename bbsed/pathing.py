import os
import platform

from .util import *

BBCF_PATH_COMPONENTS = ("steamapps", "common", "BlazBlue Centralfiction", "data", "Char")


def get_data_dir():
    """
    Get most top-level meta data directory for the app.
    If this directory does not exist we create it.
    """
    if platform.system().upper() == "WINDOWS":
        data_dir = os.path.join(os.environ["APPDATA"], "bbsed")

    else:
        data_dir = os.path.join(os.path.expanduser("~"), "bbsed")

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
    def apply_config_file(self):
        """
        Helper property to get the applied sprites config file path.
        """
        return os.path.join(self.data_dir, "apply.conf")

    @property
    def steam_exe(self):
        """
        Helper property to get our steam.exe full path based on our configured Steam install location.
        """
        return os.path.join(self.app_config["bbsed"]["steam_install"], "steam.exe")

    @property
    def bbcf_data_dir(self):
        """
        Helper property to get our BBCF install location based on our configured Steam install location.
        """
        return os.path.join(self.app_config["bbsed"]["steam_install"], *BBCF_PATH_COMPONENTS)

    def _get_sprite_cache_path(self, character):
        """
        Ensure all cached sprites the app manages are located in the same top-level directory.
        """
        return os.path.join(self.data_dir, "sprites", character)

    def get_sprite_cache_path(self, character):
        """
        Get the patch where we should cache sprites for the given character.
        """
        return self._get_sprite_cache_path(character)

    def get_sprite_cache(self, character):
        """
        Return a list of all cached sprites for this character.
        """
        sprite_cache_path = self._get_sprite_cache_path(character)
        sprite_cache = []

        for hip_image in listdir_safe(sprite_cache_path):
            # We check for the character abbreviation in the file name as some characters seem to have
            # sprite data in their PAC files that belongs to other characters? I don't understand why.
            # For now, we are not editing this information so we can just... not deal with it :D
            # Hopefully this change does not exclude any actually important sprites.
            if character in hip_image:
                hip_full_path = os.path.join(sprite_cache_path, hip_image)
                sprite_cache.append(hip_full_path)

        return sprite_cache

    @staticmethod
    def _get_path_pcs(*pcs):
        """
        Get the path pieces of a save or edit path.
        Save and edit paths both conform to the following structure:

        - <top level>
            - <character>
                - pal
                    - <palette ID>

        Note that a save path can have one further layer for the saved palette name.
        """
        path_pcs = []

        # If we have at least one piece we were given a character.
        if len(pcs) >= 1:
            character = pcs[0]
            path_pcs.append(character)

        # If we have at least two pieces then we were also given a palette ID.
        if len(pcs) >= 2:
            palette_id = pcs[1]
            path_pcs.append("pal")
            path_pcs.append(palette_id)

        # We will only get here for save paths.
        # If we have at least three pieces then we were given a palette save name.
        if len(pcs) >= 3:
            save_name = pcs[2]
            path_pcs.append(save_name)

        return path_pcs

    def _get_edit_path(self, *pcs):
        """
        Ensure all the files the app can edit are located in the same top-level directory.
        For now we assume all edit paths are for palettes.
        """
        edit_path_pcs = self._get_path_pcs(*pcs)
        return os.path.join(self.data_dir, "edit", *edit_path_pcs)

    def get_edit_palette_path(self, character, palette_id):
        """
        Get the path of a characters palette cache subdirectory.
        """
        return self._get_edit_path(character, palette_id)

    def get_game_palette(self, character, palette_id):
        """
        Get a list of HPL game-version palette files for the given character and palette ID.
        """
        character_edit_path = self._get_edit_path(character, palette_id)
        hpl_files_list = []

        for hpl_file in listdir_safe(character_edit_path):
            hpl_full_path = os.path.join(character_edit_path, hpl_file)

            # We explicitly want the backup HPL file.
            if hpl_file.endswith(BACKUP_PALETTE_EXT):
                hpl_files_list.append(hpl_full_path)

        return hpl_files_list

    def get_edit_slot_meta(self, character, palette_id):
        """
        Get the meta data file used to describe the slot name for a given palette edit.
        Used if and only if edits are being made to an existing saved palette.
        """
        character_edit_path = self._get_edit_path(character, palette_id)
        return os.path.join(character_edit_path, "slot.txt")

    def get_edit_palette(self, character, palette_id):
        """
        Get a list of HPL palette files in the edit slot for the given character and palette ID.
        """
        character_edit_path = self._get_edit_path(character, palette_id)
        hpl_files_list = []

        for hpl_file in listdir_safe(character_edit_path):
            hpl_full_path = os.path.join(character_edit_path, hpl_file)

            is_hpl = hpl_file.endswith(PALETTE_EXT)
            backup = hpl_file.endswith(BACKUP_PALETTE_EXT)

            # We ignore backup HPL files.
            if is_hpl and not backup:
                hpl_files_list.append(hpl_full_path)

        return hpl_files_list

    def get_edit_palette_hashes(self, character, palette_id):
        """
        Get a list of edit palette files combined with their current and original hashes.
        """
        hpl_files_list = self.get_edit_palette(character, palette_id)
        palette_hashes_list = []

        for hpl_full_path in hpl_files_list:
            edit_hash = hash_file(hpl_full_path)

            with open(get_hash_path(hpl_full_path), "r") as hash_fp:
                orig_hash = hash_fp.read()

            palette_hashes_list.append((hpl_full_path, edit_hash, orig_hash))

        return palette_hashes_list

    def walk_edit(self, *characters):
        """
        Iterate our top level cache directory.
        """
        if not characters:
            characters = os.listdir(self._get_edit_path())

        for character in characters:
            for palette_id, palette_num in iter_palettes():
                hpl_files_list = self.get_edit_palette(character, palette_id)

                if hpl_files_list:
                    yield character, palette_id, hpl_files_list

    def _get_save_path(self, *pcs):
        """
        Ensure all the files the app separately saves as user data are located in the same top-level directory.
        For now we assume all save paths are for palettes.
        """
        save_path_pcs = self._get_path_pcs(*pcs)
        return os.path.join(self.data_dir, "save", *save_path_pcs)

    def get_character_save_path(self, character, palette_id, save_name):
        """
        Get the palette save path for a palette. A palette is associated to a character and palette ID.
        """
        return self._get_save_path(character, palette_id, save_name)

    def get_character_saves(self, character, palette_id):
        """
        Get a list of saved palettes for the given character and palette ID.
        """
        character_save_path = self._get_save_path(character, palette_id)
        return listdir_safe(character_save_path)

    def get_saved_palette(self, character, palette_id, save_name):
        """
        Get a list of HPL palette files saved as `save_name` for the given character and palette ID.
        """
        character_save_path = self._get_save_path(character, palette_id, save_name)
        return [os.path.join(character_save_path, hpl_file) for hpl_file in os.listdir(character_save_path)]

    def walk_save(self, *characters):
        """
        Walk our top level save directory.
        """
        if not characters:
            characters = os.listdir(self._get_save_path())

        for character in characters:
            for palette_id, palette_num in iter_palettes():
                for save_name in self.get_character_saves(character, palette_id):
                    yield character, palette_id, save_name
