import os
import shutil
import traceback

from collections import defaultdict

from PyQt5 import QtCore
from libpac import extract_pac, enumerate_pac

IMAGE_FILE_FMT = "char_{}_img.pac"
PALETTE_FILE_FMT = "char_{}_pal.pac"


def get_missing_files(pac_file_path, cache_path):
    """
    Helper to get a set of missing files called out/required by a PAC file.
    These files are "required" as they are part of a character definition.
    """
    try:
        file_list = enumerate_pac(pac_file_path)
        required_files = {item[0] for item in file_list}

    # FIXME: LOL
    except Exception:
        traceback.print_exc()
        required_files = set()

    # Determine if we are missing any files that the PAC file says we need.
    existing_files = set(os.listdir(cache_path))
    missing_files = required_files - existing_files

    return missing_files


class ExtractThread(QtCore.QThread):

    message = QtCore.pyqtSignal(str)

    def __init__(self, bbcf_install, data_dir, abbreviation):
        QtCore.QThread.__init__(self)
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
            # If we dont have a backup of the original game files we should make one.
            # Realistically Steam can restore "bad" files but we should probably allow the users of the tool to do
            # that from the tool if so desired as a good UX.
            palette_backup_path = palette_file_path.replace(".pac", ".orig.pac")
            if not os.path.exists(palette_backup_path):
                self.message.emit("Backing up game palette files...")
                shutil.copyfile(palette_file_path, palette_backup_path)

            try:
                self.message.emit("Extracting HPL palette files...")
                extract_pac(palette_file_path, palette_cache_path, extract_filter=missing_hpl_files)

            # FIXME: LOL
            except Exception:
                traceback.print_exc()
                return

        # Listing this directory will include backup files if they exist. We should not iterate those to save time.
        hpl_file_list = os.listdir(palette_cache_path)
        hpl_file_list = filter(lambda _hpl_file: not _hpl_file.endswith(".orig.hpl"), hpl_file_list)

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
            hpl_backup_path = os.path.join(palette_cache_path, hpl_file.replace(".hpl", ".orig.hpl"))
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
            try:
                self.message.emit("Extracting image files...")
                extract_pac(img_file_path, image_cache_path, extract_filter=missing_hip_files)

            # FIXME: LOL
            except Exception:
                traceback.print_exc()
                return

        # Iterate our cached image files and maintain a list of the HIP files.
        # This list is used as a user-facing file list, as these are the actual game files.
        # Any PNGs generated by the tool are "internal".
        self.message.emit("Creating HIP image list...")
        for hip_image in os.listdir(image_cache_path):
            if hip_image.endswith(".hip"):
                self.hip_images.append(hip_image)

    def run(self):
        palette_cache_path = os.path.join(self.data_dir, self.abbreviation, "pal")
        image_cache_path = os.path.join(self.data_dir, self.abbreviation, "img")

        self._extract_palettes(palette_cache_path)
        self._extract_sprites(image_cache_path)
