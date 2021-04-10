import os
import shutil

from libpac import create_pac

from .work_thread import WorkThread, WorkThreadException
from .util import *


class ExportThread(WorkThread):
    def __init__(self, pac_path, paths):
        WorkThread.__init__(self)
        self.pac_path = pac_path
        self.paths = paths

    def _get_export_list(self):
        """
        Generate a list of files to export. The list is a tuple of HPL source file full paths
        and the name of the file as it is to be called within the PAC file.
        """
        files_to_export = []

        for character, palette_id, save_name in self.paths.walk_save():
            char_save_path = self.paths.get_character_save_path(character, palette_id, save_name)
            export_file_suffix = PALETTE_SAVE_MARKER + save_name + PALETTE_EXT

            for hpl_file in os.listdir(char_save_path):
                hpl_pac_name = hpl_file.replace(PALETTE_EXT, export_file_suffix)
                hpl_src_path = os.path.join(char_save_path, hpl_file)
                files_to_export.append((hpl_src_path, hpl_pac_name))

        return files_to_export

    def _create_pac_file(self, files_to_export):
        """
        Create and populate a temporary directory containing the files we want to export.
        The generate a PAC file from the contents of that directory.
        """
        # Create a temp directory which will serve as the source for our PAC file.
        with temp_directory() as temp_dir:
            for hpl_src_path, hpl_pac_name in files_to_export:
                hpl_dst_path = os.path.join(temp_dir, hpl_pac_name)
                shutil.copyfile(hpl_src_path, hpl_dst_path)

            try:
                create_pac(temp_dir, self.pac_path)

            except Exception:
                raise WorkThreadException("Error Creating PAC File", f"Failed to create PAC file from HPL file list!")

    def work(self):
        files_to_export = self._get_export_list()
        self._create_pac_file(files_to_export)
