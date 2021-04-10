import os
import shutil

from libpac import create_pac

from .work_thread import WorkThread, WorkThreadException
from .util import *


class ApplyThread(WorkThread):
    def __init__(self, files_to_apply, paths):
        WorkThread.__init__(self)
        self.files_to_apply = files_to_apply
        self.paths = paths

    def _apply_palettes(self, temp_dir, character, selected_palettes, hpl_file_list):
        """
        Gather our HPL files for the given character and generate a PAC file to be copied to the BBCF
        game data directory. For any palettes not explicitly selected by the user we will insert the game
        version of the palette into the PAC file so we create a full valid character palette file.
        """
        pac_file_name = PALETTE_FILE_FMT.format(character)
        pac_full_path = os.path.join(self.paths.bbcf_data_dir, pac_file_name)

        # Copy the user selected palettes to the temp directory.
        for hpl_full_path in hpl_file_list:
            temp_hpl_file = os.path.basename(hpl_full_path)
            shutil.copyfile(hpl_full_path, os.path.join(temp_dir, temp_hpl_file))

        # Copy game-version-palettes to the temp directory as necessary.
        for palette_num in range(GAME_MAX_PALETTES):
            palette_id = palette_number_to_id(palette_num)

            # Only include game-version palettes if the user did not make a selection for this palette ID.
            if palette_id not in selected_palettes:
                for hpl_full_path in self.paths.get_game_palette(character, palette_id):
                    temp_hpl_file = os.path.basename(hpl_full_path).replace(BACKUP_PALETTE_EXT, PALETTE_EXT)
                    shutil.copyfile(hpl_full_path, os.path.join(temp_dir, temp_hpl_file))

        try:
            # Create a PAC file with the temp directory as the source.
            self.message.emit(f"Creating {pac_file_name}...")
            create_pac(temp_dir, pac_full_path)

        except Exception:
            raise WorkThreadException("Error Creating PAC File",
                                      f"Failed to create PAC file from HIP file list!")

    def work(self):
        self.message.emit("Gathering HPL palette files...")
        for character, (selected_palettes, hpl_file_list) in self.files_to_apply.items():
            # We have a helper method mostly so we can apply all these palettes within the temp_directory block
            # but not have to have the extra indentation.
            with temp_directory() as temp_dir:
                self._apply_palettes(temp_dir, character, selected_palettes, hpl_file_list)
