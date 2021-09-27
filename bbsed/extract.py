import os
import shutil

from libpac import extract_pac, enumerate_pac
from libjonb import extract_collision_boxes
from libscr import parse_script

from .work_thread import WorkThread, AppException
from .util import *


def get_missing_files(pac_file_path, existing_files):
    """
    Helper to get a set of missing files called out/required by a PAC file.
    These files are "required" as they are part of a character definition.
    """
    base_name = os.path.basename(pac_file_path)

    try:
        file_list = enumerate_pac(pac_file_path)
        required_files = {item[0] for item in file_list}

    except Exception:
        raise AppException("Error Enumerating PAC File", f"Failed to get files list from {base_name}!")

    # Determine if we are missing any files that the PAC file says we need.
    existing_files = set(existing_files)
    missing_files = required_files - existing_files

    return missing_files


def missing_file_filter(missing_files):
    """
    Helper to create a filter function for extract_pac based on a set of missing files.
    """
    def _filter_func(file_entry):
        return file_entry[0] in missing_files

    return _filter_func


def exclude_extra_palettes(missing_hpl_files):
    """
    The game only shows palettes 1-24, but there are files for more palettes than that.
    Ignore palettes with a greater palette ID than 24 as they are not usable in game.
    """
    for hpl_file in list(missing_hpl_files):
        palette_num = hpl_file[CHAR_ABBR_LEN:CHAR_ABBR_LEN+PALETTE_ID_LEN]

        # Palette number is 0-23 so `palette_num` >= `GAME_MAX_PALETTES` is our filter.
        if int(palette_num) >= GAME_MAX_PALETTES:
            missing_hpl_files.remove(hpl_file)


class ExtractThread(WorkThread):
    def __init__(self, character, paths):
        WorkThread.__init__(self)
        self.character = character
        self.paths = paths

    def _extract_palettes(self):
        """
        Helper to extract HPL palette files and dump them to `palette_edit_path`.
        """
        existing_hpl_files = []
        for _, __, hpl_files_list in self.paths.walk_edit(self.character):
            existing_hpl_files.extend([os.path.basename(hpl_full_path) for hpl_full_path in hpl_files_list])

        palette_file_name = GAME_PALETTE_FILE_FMT.format(self.character)
        palette_file_path = os.path.join(self.paths.bbcf_data_dir, palette_file_name)

        # Get the file name for the palette PAC file associated to the given character.
        # We look for the backup file first as we want to extract data from the original source
        # and not from files the tool itself has modified.
        backup_file_name = palette_file_name.replace(PALETTE_EXT, BACKUP_PALETTE_EXT)
        backup_file_path = os.path.join(self.paths.bbcf_data_dir, backup_file_name)

        # If the backup file does not exist we assume the game files are unmodified by the tool.
        if os.path.exists(backup_file_path):
            palette_file_path = backup_file_path

        self.message.emit("Looking for missing HPL files...")
        missing_hpl_files = get_missing_files(palette_file_path, existing_hpl_files)
        exclude_extra_palettes(missing_hpl_files)

        # Only perform a PAC extraction if we are missing any files called out in the PAC.
        if missing_hpl_files:
            hpl_file_filter = missing_file_filter(missing_hpl_files)

            # If we dont have a backup of the original game files we should make one.
            # Realistically Steam can restore "bad" files but we should probably allow the users of the tool to do
            # that from the tool if so desired as a good UX.
            palette_backup_path = palette_file_path.replace(GAME_PALETTE_EXT, BACKUP_GAME_PALETTE_EXT)
            if not os.path.exists(palette_backup_path):
                self.message.emit("Backing up game palette files...")
                shutil.copyfile(palette_file_path, palette_backup_path)

            # Extract the PAC to a temporary location that will be deleted when we are done.
            with temp_directory() as temp_dir:
                try:
                    self.message.emit("Extracting HPL palette files...")
                    extract_pac(palette_file_path, temp_dir, extract_filter=hpl_file_filter)

                except Exception:
                    message = f"Failed to extract HPL files from {palette_file_name}!"
                    raise AppException("Error Extracting PAC File", message)

                # Extract new palettes to the edit palette directory for this character.
                self.message.emit("Creating HPL palette file meta data...")
                for hpl_file in os.listdir(temp_dir):
                    hpl_src_path = os.path.join(temp_dir, hpl_file)
                    palette_num = hpl_file[CHAR_ABBR_LEN:CHAR_ABBR_LEN+PALETTE_ID_LEN]
                    palette_id = palette_number_to_id(palette_num)

                    palette_edit_path = self.paths.get_edit_palette_path(self.character, palette_id)

                    # If our edit path doesnt exist yet we should make it..
                    if not os.path.exists(palette_edit_path):
                        os.makedirs(palette_edit_path)

                    # On extract of a palette we create a backup/original version at the same time
                    # we create the file which we expose to the user for editing.
                    hpl_dst_path = os.path.join(palette_edit_path, hpl_file)
                    shutil.copyfile(hpl_src_path, hpl_dst_path.replace(PALETTE_EXT, BACKUP_PALETTE_EXT))
                    shutil.copyfile(hpl_src_path, hpl_dst_path)

                    # Additionally we save a hash of the backup/original version of the palette.
                    with open(get_hash_path(hpl_dst_path), "w") as hash_fp:
                        hash_fp.write(hash_file(hpl_src_path))

    def _extract_images(self, cache_path, file_fmt):
        """
        Helper method to extract HIP files from a PAC file.
        """
        # If our cache directory doesn't exist we should create it.
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        # Get the file name for the PAC file associated to the the character `self.character`.
        hip_file_name = file_fmt.format(self.character)
        hip_file_path = os.path.join(self.paths.bbcf_data_dir, hip_file_name)

        self.message.emit("Looking for missing HIP files...")
        missing_hip_files = get_missing_files(hip_file_path, os.listdir(cache_path))

        # Only perform a PAC extraction if we are missing any files called out in the PAC.
        if missing_hip_files:
            hip_file_filter = missing_file_filter(missing_hip_files)

            try:
                self.message.emit("Extracting image files...")
                extract_pac(hip_file_path, cache_path, extract_filter=hip_file_filter)

            except Exception:
                message = f"Failed to extract HIP files from {hip_file_name}!"
                raise AppException("Error Extracting PAC File", message)

    def _extract_sprites(self):
        """
        Helper to extract sprite HIP image files and dump them to the cache path for the selected character.
        """
        sprite_cache_path = self.paths.get_sprite_cache_path(self.character)
        self._extract_images(sprite_cache_path, GAME_SPRITE_FILE_FMT)
        self._extract_images(sprite_cache_path, GAME_EFFECT_FILE_FMT)

    def _extract_scripts(self):
        """
        Helper method to extract SCR files from a PAC file and dump them to the cache path in JSON format.
        """
        script_cache_path = self.paths.get_script_cache_path(self.character)

        # If our cache directory doesn't exist we should create it.
        if not os.path.exists(script_cache_path):
            os.makedirs(script_cache_path)

        # Get the file name for the PAC file associated to the the character `self.character`.
        scr_file_name = GAME_SCRIPT_FILE_FMT.format(self.character)
        scr_file_path = os.path.join(self.paths.bbcf_data_dir, scr_file_name)

        self.message.emit("Looking for missing script files...")
        existing_scr_files = [file_name.replace(".json", ".bin") for file_name in os.listdir(script_cache_path)]
        missing_scr_files = get_missing_files(scr_file_path, existing_scr_files)

        # Only perform a PAC extraction if we are missing any files called out in the PAC.
        if missing_scr_files:
            scr_file_filter = missing_file_filter(missing_scr_files)

            # Extract the PAC to a temporary location that will be deleted when we are done.
            with temp_directory() as temp_dir:
                try:
                    self.message.emit("Extracting script files...")
                    extract_pac(scr_file_path, temp_dir, extract_filter=scr_file_filter)

                except Exception:
                    message = f"Failed to extract script files from {scr_file_name}!"
                    raise AppException("Error Extracting PAC File", message)

                # Extract new palettes to the edit palette directory for this character.
                self.message.emit("Creating script file meta data...")
                for scr_file in os.listdir(temp_dir):
                    scr_src_path = os.path.join(temp_dir, scr_file)
                    scr_dst_path = os.path.join(script_cache_path, scr_file.replace(".bin", ".json"))

                    try:
                        parse_script(scr_src_path, scr_dst_path)

                    except Exception:
                        message = f"Failed to parse {scr_file}!"
                        raise AppException("Error Parsing Script File", message)

    def _exctract_collisions(self):
        """
        Helper method to extract JONBIN files from a PAC file and dump them to the cache path in JSON format.
        """
        collision_cache_path = self.paths.get_collision_cache_path(self.character)

        # If our cache directory doesn't exist we should create it.
        if not os.path.exists(collision_cache_path):
            os.makedirs(collision_cache_path)

        # Get the file name for the PAC file associated to the the character `self.character`.
        jonb_file_name = GAME_COLLISION_FILE_FMT.format(self.character)
        jonb_file_path = os.path.join(self.paths.bbcf_data_dir, jonb_file_name)

        self.message.emit("Looking for missing collision box files...")
        existing_jonb_files = [file_name.replace(".json", ".jonbin") for file_name in os.listdir(collision_cache_path)]
        missing_jonb_files = get_missing_files(jonb_file_path, existing_jonb_files)

        # Only perform a PAC extraction if we are missing any files called out in the PAC.
        if missing_jonb_files:
            jonb_file_filter = missing_file_filter(missing_jonb_files)

            # Extract the PAC to a temporary location that will be deleted when we are done.
            with temp_directory() as temp_dir:
                try:
                    self.message.emit("Extracting collision box files...")
                    extract_pac(jonb_file_path, temp_dir, extract_filter=jonb_file_filter)

                except Exception:
                    message = f"Failed to extract collision box files from {jonb_file_name}!"
                    raise AppException("Error Extracting PAC File", message)

                # Extract new palettes to the edit palette directory for this character.
                self.message.emit("Creating collision box file meta data...")
                for jonb_file in os.listdir(temp_dir):
                    jonb_src_path = os.path.join(temp_dir, jonb_file)
                    jonb_dst_path = os.path.join(collision_cache_path, jonb_file.replace(".jonbin", ".json"))
                    extract_collision_boxes(jonb_src_path, jonb_dst_path)

    def work(self):
        self._extract_palettes()
        self._extract_sprites()
        self._extract_scripts()
        self._exctract_collisions()
