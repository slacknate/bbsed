import os
import shutil

from libpac import create_pac

from .work_thread import WorkThread, AppException
from .util import *


class ExportThread(WorkThread):
    def __init__(self, pac_path, files_to_export, paths):
        WorkThread.__init__(self)
        self.files_to_export = files_to_export
        self.pac_path = pac_path
        self.paths = paths

    def _get_export_list(self):
        """
        Generate a list of files to export. The list is a tuple of HPL source file full paths
        and the name of the file as it is to be called within the PAC file.
        """
        export_list = []

        for character, palette_info in self.files_to_export.items():
            for palette_id, select_info in palette_info.items():
                for export_name, hpl_file_list in select_info.items():
                    for hpl_src_path in hpl_file_list:
                        hpl_file = os.path.basename(hpl_src_path)

                        if export_name == SLOT_NAME_EDIT:
                            export_file_suffix = PALETTE_EDIT_MARKER + PALETTE_EXT
                        else:
                            export_file_suffix = PALETTE_SAVE_MARKER + export_name + PALETTE_EXT

                        hpl_pac_name = hpl_file.replace(PALETTE_EXT, export_file_suffix)
                        export_list.append((hpl_src_path, hpl_pac_name))

        return export_list

    def _create_pac_file(self, export_list):
        """
        Create and populate a temporary directory containing the files we want to export.
        The generate a PAC file from the contents of that directory.
        """
        # Create a temp directory which will serve as the source for our PAC file.
        with temp_directory() as temp_dir:
            for hpl_src_path, hpl_pac_name in export_list:
                hpl_dst_path = os.path.join(temp_dir, hpl_pac_name)
                shutil.copyfile(hpl_src_path, hpl_dst_path)

            try:
                create_pac(temp_dir, self.pac_path)

            except Exception:
                raise AppException("Error Creating PAC File", f"Failed to create PAC file from HPL file list!")

    def work(self):
        export_list = self._get_export_list()
        self._create_pac_file(export_list)
