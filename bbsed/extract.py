import os
import shutil

from libpac import extract_pac, enumerate_pac

from .work_thread import WorkThread, WorkThreadException
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
        raise WorkThreadException("Error Enumerating PAC File", f"Failed to get files list from {base_name}!")

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


def hpl_filter_func(hpl_file):
    """
    Filter function to exclude palette backups and dirty files from the palette info dict.
    """
    return not hpl_file.endswith(BACKUP_PALETTE_EXT) and not hpl_file.endswith(DIRTY_PALETTE_EXT)


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

        # Get the file name for the palette PAC file associated to the given character.
        palette_file_name = PALETTE_FILE_FMT.format(self.character)
        palette_file_path = os.path.join(self.paths.bbcf_data_dir, palette_file_name)

        self.message.emit("Looking for missing HPL files...")
        missing_hpl_files = get_missing_files(palette_file_path, existing_hpl_files)

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
                    raise WorkThreadException("Error Extracting PAC File", message)

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

                    # This is the first extraction of the palettes.
                    # We create the backup/original version of the palette as well as the file which will be edited.
                    hpl_dst_path = os.path.join(palette_edit_path, hpl_file)
                    shutil.copyfile(hpl_src_path, hpl_dst_path.replace(PALETTE_EXT, BACKUP_PALETTE_EXT))
                    shutil.copyfile(hpl_src_path, hpl_dst_path)

    def _extract_sprites(self):
        """
        Helper to extract HIP image files and dump them to the cache path for the selected character.
        """
        sprite_cache_path = self.paths.get_sprite_cache_path(self.character)
 
        # If our cache directory doesn't exist we should create it.
        if not os.path.exists(sprite_cache_path):
            os.makedirs(sprite_cache_path)

        # Get the file name for the sprite PAC file associated to the the character `self.character`.
        sprite_file_name = SPRITE_FILE_FMT.format(self.character)
        sprite_file_path = os.path.join(self.paths.bbcf_data_dir, sprite_file_name)

        self.message.emit("Looking for missing HIP files...")
        missing_hip_files = get_missing_files(sprite_file_path, os.listdir(sprite_cache_path))

        # Only perform a PAC extraction if we are missing any files called out in the PAC.
        if missing_hip_files:
            hip_file_filter = missing_file_filter(missing_hip_files)

            try:
                self.message.emit("Extracting image files...")
                extract_pac(sprite_file_path, sprite_cache_path, extract_filter=hip_file_filter)

            except Exception:
                message = f"Failed to extract HIP files from {sprite_file_name}!"
                raise WorkThreadException("Error Extracting PAC File", message)

    def work(self):
        self._extract_palettes()
        self._extract_sprites()
