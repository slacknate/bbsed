import os
import shutil

from libpac import create_pac

from .work_thread import WorkThread, AppException
from .util import *


def iter_info(palette_info):
    """
    Helper to get our HPL file full paths out of the palette into.
    This amount of iteration looks scarier than it is.
    Note that palette IDs are the keys to the `palette_info` dict.
    For our apply operation each character will have at most one palette selected per palette ID.
    This means that after the first time fully iterate an `hpl_file_list` the entire iterator is done.
    """
    for select_info in palette_info.values():
        for hpl_file_list in select_info.values():
            for hpl_full_path in hpl_file_list:
                yield hpl_full_path


class ApplyThread(WorkThread):
    def __init__(self, files_to_apply, paths):
        WorkThread.__init__(self)
        self.files_to_apply = files_to_apply
        self.paths = paths

    def _apply_palettes(self, temp_dir, character, palette_info):
        """
        Gather our HPL files for the given character and generate a PAC file to be copied to the BBCF
        game data directory. For any palettes not explicitly selected by the user we will insert the game
        version of the palette into the PAC file so we create a full valid character palette file.
        """
        self.message.emit("Gathering HPL palette files...")

        pac_file_name = PALETTE_FILE_FMT.format(character)
        pac_full_path = os.path.join(self.paths.bbcf_data_dir, pac_file_name)

        # Copy the user selected palettes to the temp directory.
        for hpl_full_path in iter_info(palette_info):
            temp_hpl_file = os.path.basename(hpl_full_path)
            shutil.copyfile(hpl_full_path, os.path.join(temp_dir, temp_hpl_file))

        # Copy game-version-palettes to the temp directory as necessary.
        for palette_num in range(GAME_MAX_PALETTES):
            palette_id = palette_number_to_id(palette_num)

            # Only include game-version palettes if the user did not make a selection for this palette ID.
            if palette_id not in palette_info:
                for hpl_full_path in self.paths.get_game_palette(character, palette_id):
                    temp_hpl_file = os.path.basename(hpl_full_path).replace(BACKUP_PALETTE_EXT, PALETTE_EXT)
                    shutil.copyfile(hpl_full_path, os.path.join(temp_dir, temp_hpl_file))

        try:
            # Create a PAC file with the temp directory as the source.
            self.message.emit(f"Creating {pac_file_name}...")
            create_pac(temp_dir, pac_full_path)

        except Exception:
            raise AppException("Error Creating PAC File", "Failed to create PAC file from HIP file list!")

    def work(self):
        for character, palette_info in self.files_to_apply.items():
            # We have a helper method mostly so we can apply all these palettes within the temp_directory block
            # but not have to have the extra indentation.
            with temp_directory() as temp_dir:
                self._apply_palettes(temp_dir, character, palette_info)
