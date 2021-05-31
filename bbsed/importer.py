import os
import shutil

from libpac import extract_pac

from .work_thread import WorkThread, AppException
from .util import *


class ImportThread(WorkThread):
    def __init__(self, hpl_to_import, pac_to_import, paths):
        WorkThread.__init__(self)
        self.hpl_to_import = hpl_to_import
        self.pac_to_import = pac_to_import
        self.paths = paths

    def _process_meta_data(self, character, palette_id, hpl_file, save_name):
        """
        Helper method to process any meta data present in the source HPL file name.
        This method returns the destination file path to which this HPL file should be copied.
        """
        if save_name == EDIT_INTERNAL_NAME:
            character_edit_path = self.paths.get_edit_palette_path(character, palette_id)

            hpl_dst_path = os.path.join(character_edit_path, hpl_file)
            hpl_dst_path = hpl_dst_path.replace(PALETTE_EDIT_MARKER, "")

        else:
            character_save_path = self.paths.get_character_save_path(character, palette_id, save_name)

            hpl_dst_path = os.path.join(character_save_path, hpl_file)
            hpl_dst_path = hpl_dst_path.split(PALETTE_SAVE_MARKER)[0]

            # If our HPL file to import features a save marker then string the split above removes the file extension.
            # We should add it back if it does not exist in our destination path.
            if not hpl_dst_path.endswith(PALETTE_EXT):
                hpl_dst_path += PALETTE_EXT

        return hpl_dst_path

    def _get_palettes_hpl(self):
        """
        Helper method to handle the import of palettes in the form of HPL files.
        """
        hpl_import_files = []

        # Check all the selected files for validity before attempting import.
        self.message.emit("Validating HPL palette files...")
        for (character, palette_id, save_name), hpl_files_list in self.hpl_to_import.items():
            for hpl_src_path in hpl_files_list:
                hpl_file = os.path.basename(hpl_src_path)
                hpl_dst_path = self._process_meta_data(character, palette_id, hpl_file, save_name)
                hpl_import_files.append((hpl_src_path, hpl_dst_path))

        return hpl_import_files

    def _get_palettes_pac(self, temp_dir):
        """
        Helper method to handle the import of palettes in the form of PAC files.
        """
        hpl_import_files = []

        self.message.emit("Extracting PAC palette files...")
        for pac_full_path, file_info in self.pac_to_import.items():
            try:
                extract_pac(pac_full_path, temp_dir)

            except Exception:
                message = f"Failed to extract HPL files from {pac_full_path}!"
                raise AppException("Error Extracting PAC File", message)

            for (character, palette_id, save_name), hpl_file_list in file_info.items():
                for hpl_file in hpl_file_list:
                    hpl_src_path = os.path.join(temp_dir, hpl_file)
                    hpl_dst_path = self._process_meta_data(character, palette_id, hpl_file, save_name)
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
