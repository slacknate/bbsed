import os
import re
import shutil

from libpac import extract_pac, enumerate_pac

from .work_thread import WorkThread, WorkThreadException, WorkThreadError
from .char_info import VALID_CHARACTERS
from .util import *

HPL_IMPORT_REGEX = re.compile(r"([a-z]{2})(\d{2})_(\d{2})(" + PALETTE_SAVE_MARKER + r"\w+)?" + PALETTE_EXT)
HPL_SAVE_REGEX = re.compile(PALETTE_SAVE_MARKER + r"(\w+)" + PALETTE_EXT)
# The game only allows the user to pick palettes 1-24, but palettes 25 and 26 exist in the files? Weird.
HPL_MAX_PALETTES = GAME_MAX_PALETTES - 1
HPL_MAX_FILES_PER_PALETTE = 7


class ImportThread(WorkThread):
    def __init__(self, hpl_file_list, pac_file_list, save_name_map, paths):
        WorkThread.__init__(self)
        self.hpl_file_list = hpl_file_list
        self.pac_file_list = pac_file_list
        self.save_name_map = save_name_map
        self.paths = paths

    @staticmethod
    def _validate_hpl_file(hpl_file):
        """
        Helper method to ensure the given HPL palette file is valid to the best of our ability.
        """
        # Assert that the import HPL file has the correct extension.
        if not hpl_file.endswith(PALETTE_EXT):
            message = "Imported HPL palettes must have extension '.hpl'!"
            raise WorkThreadError("Invalid HPL palette file!", message)

        # Assert that imported HPL files must have file names that match the names we would see in
        # game data so we know which cache directory to import the files to.
        format_match = HPL_IMPORT_REGEX.search(hpl_file)
        if format_match is None:
            message = "Imported HPL palettes must have name format matching game data!\n\nExample:\n\nam00_00.hpl"
            raise WorkThreadError("Invalid HPL palette file!", message)

        # Assert that the file name starts with a valid character abbreviation.
        # If it does not we cannot know where to put the data in the cache or where to apply the file
        # to the actual game data.
        abbreviation = format_match.group(1)
        if abbreviation not in VALID_CHARACTERS:
            message = f"HPL file name {hpl_file} does not begin with a known character abbreviation!"
            raise WorkThreadError("Invalid HPL palette file!", message)

        # Assert that the palette index is valid.
        palette_index = int(format_match.group(2))
        if palette_index < 0 or palette_index > HPL_MAX_PALETTES:
            message = f"HPL palette index must 00 to {HPL_MAX_PALETTES}!"
            raise WorkThreadError("Invalid HPL palette file!", message)

        # Assert that the palette file number is valid.
        file_number = int(format_match.group(3))
        if file_number < 0 or file_number > HPL_MAX_FILES_PER_PALETTE:
            message = f"HPL file number must be 00 to {HPL_MAX_FILES_PER_PALETTE:02}!"
            raise WorkThreadError("Invalid HPL palette file!", message)

    def _import_from_marker(self, hpl_file):
        """
        Import an HPL that has a name containing a bbsed save marker.
        This allows us to determine where to put the file from the HPL file name.
        """
        character = hpl_file[:CHAR_ABBR_LEN]

        palette_number = hpl_file[CHAR_ABBR_LEN:CHAR_ABBR_LEN+PALETTE_ID_LEN]
        palette_id = palette_number_to_id(palette_number)

        match = HPL_SAVE_REGEX.search(hpl_file)
        save_ext = match.group(0)
        save_name = match.group(1)

        char_save_path = self.paths.get_character_save_path(character, palette_id, save_name)
        hpl_file = hpl_file.replace(save_ext, PALETTE_EXT)
        hpl_dst_path = os.path.join(char_save_path, hpl_file)
        return hpl_dst_path

    def _import_from_map(self, hpl_file):
        """
        Import an HPL file that does not have a name containing a bbsed save marker.
        However, we asked the user to name this import so we can grab the save name from that map.
        """
        character = hpl_file[:CHAR_ABBR_LEN]

        palette_number = hpl_file[CHAR_ABBR_LEN:CHAR_ABBR_LEN+PALETTE_ID_LEN]
        palette_id = palette_number_to_id(palette_number)

        char_pal_id = hpl_file[:CHAR_ABBR_LEN+PALETTE_ID_LEN]
        save_name = self.save_name_map[char_pal_id]

        char_save_path = self.paths.get_character_save_path(character, palette_id, save_name)
        hpl_dst_path = os.path.join(char_save_path, hpl_file)
        return hpl_dst_path

    def _get_palettes_hpl(self):
        """
        Helper method to handle the import of palettes in the form of HPL files.
        """
        hpl_import_files = []

        # Check all the selected files for validity before attempting import.
        self.message.emit("Validating HPL palette files...")
        for hpl_src_path in self.hpl_file_list:
            hpl_file = os.path.basename(hpl_src_path)
            self._validate_hpl_file(hpl_file)

            if PALETTE_SAVE_MARKER in hpl_file:
                hpl_dst_path = self._import_from_marker(hpl_file)
            else:
                hpl_dst_path = self._import_from_map(hpl_file)

            hpl_import_files.append((hpl_src_path, hpl_dst_path))

        return hpl_import_files

    def _get_palettes_pac(self, temp_dir):
        """
        Helper method to handle the import of palettes in the form of PAC files.
        """
        pac_import_files = []
        hpl_import_files = []

        self.message.emit("Validating PAC palette files...")
        for pac_full_path in self.pac_file_list:
            hpl_files_list = enumerate_pac(pac_full_path)

            for hpl_file, _, __, ___ in hpl_files_list:
                self._validate_hpl_file(hpl_file)

            pac_import_files.append(pac_full_path)

        self.message.emit("Extracting PAC palette files...")
        for pac_full_path in pac_import_files:
            try:
                extract_pac(pac_full_path, temp_dir)

            except Exception:
                message = f"Failed to extract HPL files from {pac_full_path}!"
                raise WorkThreadException("Error Extracting PAC File", message)

            for hpl_file in os.listdir(temp_dir):
                hpl_src_path = os.path.join(temp_dir, hpl_file)

                if PALETTE_SAVE_MARKER in hpl_file:
                    hpl_dst_path = self._import_from_marker(hpl_file)
                else:
                    hpl_dst_path = self._import_from_map(hpl_file)

                hpl_import_files.append((hpl_src_path, hpl_dst_path))

        return hpl_import_files

    @staticmethod
    def _import_hpl_files(hpl_import_files):
        """
        Helper to copy the HPL files we want to import from their existing location to the palette cache directory.
        """
        for hpl_src_path, hpl_dst_path in hpl_import_files:
            hpl_dst_dir = os.path.dirname(hpl_dst_path)

            # If our destination directory does not exist we should create it before attempting the import.
            if not os.path.exists(hpl_dst_dir):
                os.makedirs(hpl_dst_dir)

            shutil.copyfile(hpl_src_path, hpl_dst_path)

    def work(self):
        # We only need the temp directory for PAC import.
        # But creating it for all cases probably does not have a noticeable performance hit.
        with temp_directory() as temp_dir:
            hpl_import_files = []

            hpl_import_files.extend(self._get_palettes_hpl())
            hpl_import_files.extend(self._get_palettes_pac(temp_dir))

            # If we got here then our files are valid! Perform the actual import.
            self._import_hpl_files(hpl_import_files)
