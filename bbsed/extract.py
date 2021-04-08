import os
import shutil

from collections import defaultdict

from libpac import extract_pac, enumerate_pac

from .work_thread import WorkThread, WorkThreadException
from .util import *


def get_missing_files(pac_file_path, cache_path):
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
    existing_files = set(os.listdir(cache_path))
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
    def __init__(self, bbcf_install, data_dir, abbreviation):
        WorkThread.__init__(self)
        self.abbreviation = abbreviation
        self.bbcf_install = bbcf_install
        self.data_dir = data_dir

        self.hip_images = []
        self.palette_info = defaultdict(list)

    def _extract_palettes(self, palette_cache_path):
        """
        Helper to extract HPL palette files and dump them to `palette_cache_path`.
        """
        # If our cache directory doesn't exist we should create it.
        if not os.path.exists(palette_cache_path):
            os.makedirs(palette_cache_path)

        # Get the file name for the palette PAC file associated to the the character `self.abbreviation`.
        palette_file_name = PALETTE_FILE_FMT.format(self.abbreviation)
        palette_file_path = os.path.join(self.bbcf_install, "data", "Char", palette_file_name)

        self.message.emit("Looking for missing HPL files...")
        missing_hpl_files = get_missing_files(palette_file_path, palette_cache_path)

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

            try:
                self.message.emit("Extracting HPL palette files...")
                extract_pac(palette_file_path, palette_cache_path, extract_filter=hpl_file_filter)

            except Exception:
                message = f"Failed to extract HPL files from {palette_file_name}!"
                raise WorkThreadException("Error Extracting PAC File", message)

        # Listing this directory will include backup files if they exist. We should not iterate those to save time.
        hpl_file_list = os.listdir(palette_cache_path)
        hpl_file_list = filter(hpl_filter_func, hpl_file_list)

        # Iterate our cached palette files and create a mapping of palette IDs to a list of associated files.
        # A palette ID is the in-game palette number you choose at character select.
        self.message.emit("Creating HPL palette file meta data...")
        for hpl_file in hpl_file_list:
            palette_num = hpl_file[2:4]
            palette_num_in_game = int(palette_num) + 1
            palette_id = f"{palette_num_in_game:02}"
            self.palette_info[palette_id].append(hpl_file)

            # Back up our HPL palette file if we have not already.
            # We create backups of these files so we can restore the game-provided content if desired.
            hpl_backup_path = os.path.join(palette_cache_path, hpl_file.replace(PALETTE_EXT, BACKUP_PALETTE_EXT))
            if not os.path.exists(hpl_backup_path):
                hpl_file_path = os.path.join(palette_cache_path, hpl_file)
                shutil.copyfile(hpl_file_path, hpl_backup_path)

    def _extract_sprites(self, image_cache_path):
        """
        Helper to extract HIP image files and dump them to `image_cache_path`.
        """
        # If our cache directory doesn't exist we should create it.
        if not os.path.exists(image_cache_path):
            os.makedirs(image_cache_path)

        # Get the file name for the sprite PAC file associated to the the character `self.abbreviation`.
        img_file_name = IMAGE_FILE_FMT.format(self.abbreviation)
        img_file_path = os.path.join(self.bbcf_install, "data", "Char", img_file_name)

        self.message.emit("Looking for missing HIP files...")
        missing_hip_files = get_missing_files(img_file_path, image_cache_path)

        # Only perform a PAC extraction if we are missing any files called out in the PAC.
        if missing_hip_files:
            hip_file_filter = missing_file_filter(missing_hip_files)

            try:
                self.message.emit("Extracting image files...")
                extract_pac(img_file_path, image_cache_path, extract_filter=hip_file_filter)

            except Exception:
                message = f"Failed to extract HIP files from {img_file_name}!"
                raise WorkThreadException("Error Extracting PAC File", message)

        # Iterate our cached image files and maintain a list of the HIP files.
        # This list is used as a user-facing file list, as these are the actual game files.
        # Any PNGs generated by the tool are "internal".
        self.message.emit("Creating HIP image list...")
        for hip_image in os.listdir(image_cache_path):
            # We check for the character abbreviation in the file name as some characters seem to have
            # sprite data in their PAC files that belongs to other characters? I don't understand why.
            # For now, we are not editing this information so we can just... not deal with it :D
            # Hopefully this change does not exclude any actually important sprites.
            if hip_image.endswith(".hip") and self.abbreviation in hip_image:
                self.hip_images.append(hip_image)

    def work(self):
        palette_cache_path = os.path.join(self.data_dir, self.abbreviation, "pal")
        image_cache_path = os.path.join(self.data_dir, self.abbreviation, "img")

        self._extract_palettes(palette_cache_path)
        self._extract_sprites(image_cache_path)
