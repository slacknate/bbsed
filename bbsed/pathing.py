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
        Set reference to our Configuration object.
        For use in the Configuration constructor.
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
        return os.path.join(self.app_config.steam_install, "steam.exe")

    @property
    def bbcf_data_dir(self):
        """
        Helper property to get our BBCF install location based on our configured Steam install location.
        """
        return os.path.join(self.app_config.steam_install, *BBCF_PATH_COMPONENTS)

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

        if os.path.exists(sprite_cache_path):
            for hip_image in os.listdir(sprite_cache_path):
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

        edit_files_list = []
        if os.path.exists(character_edit_path):
            edit_files_list = os.listdir(character_edit_path)

        for hpl_file in edit_files_list:
            hpl_full_path = os.path.join(character_edit_path, hpl_file)

            if hpl_file.endswith(BACKUP_PALETTE_EXT):
                hpl_files_list.append(hpl_full_path)

        return hpl_files_list

    def get_edit_palette(self, character, palette_id):
        """
        Get a list of HPL palette files in the edit slot for the given character and palette ID.
        """
        character_edit_path = self._get_edit_path(character, palette_id)
        hpl_files_list = []

        edit_files_list = []
        if os.path.exists(character_edit_path):
            edit_files_list = os.listdir(character_edit_path)

        for hpl_file in edit_files_list:
            hpl_full_path = os.path.join(character_edit_path, hpl_file)

            dirty = hpl_file.endswith(DIRTY_PALETTE_EXT)
            backup = hpl_file.endswith(BACKUP_PALETTE_EXT)

            # For palette files associated to this palette we include the dirty versions if they exist
            # and only include non-dirty versions of the palette files if a dirty version does not exist.
            # NOTE: Right now we can only edit palette file nnXX_00.hpl as we have not yet created a mapping
            #       that defines what sprites/data the other files are associated to, so for the time being
            #       we will only ever have a dirty version of this first palette file from each PAC file.
            # We purposefully do not include backup files in the hpl files list.
            dirty_exists = os.path.exists(hpl_full_path.replace(PALETTE_EXT, DIRTY_PALETTE_EXT))

            if (dirty or (not dirty and not dirty_exists)) and not backup:
                hpl_files_list.append(hpl_full_path)

        return hpl_files_list

    def walk_edit(self, *characters):
        """
        Iterate our top level cache directory.
        """
        if not characters:
            characters = os.listdir(self._get_edit_path())

        for character in characters:
            for palette_num in range(GAME_MAX_PALETTES):
                palette_id = palette_number_to_id(palette_num)

                char_edit_path = self._get_edit_path(character, palette_id)

                if os.path.exists(char_edit_path):
                    hpl_files_list = [os.path.join(char_edit_path, hpl_file) for hpl_file in os.listdir(char_edit_path)]
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

        save_names = []
        if os.path.exists(character_save_path):
            save_names = list(os.listdir(character_save_path))

        return save_names

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
            for palette_num in range(GAME_MAX_PALETTES):
                palette_id = palette_number_to_id(palette_num)

                pal_save_path = self._get_save_path(character, palette_id)

                if os.path.exists(pal_save_path):
                    for save_name in os.listdir(pal_save_path):
                        yield character, palette_id, save_name
