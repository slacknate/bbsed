import os
import shutil

from libpac import create_pac

from .work_thread import WorkThread, WorkThreadException
from .util import *


class ExportThread(WorkThread):
    def __init__(self, pac_path, files_to_export):
        WorkThread.__init__(self)
        self.files_to_export = files_to_export
        self.pac_path = pac_path

    def work(self):
        # Create a temp directory which will serve as the source for our PAC file.
        with temp_directory() as temp_dir:
            for hpl_src_path in self.files_to_export:
                hpl_file = os.path.basename(hpl_src_path)

                # Ensure we replace the dirty extension so we can safely export dirty palettes.
                hpl_dst_path = os.path.join(temp_dir, hpl_file).replace(DIRTY_PALETTE_EXT, PALETTE_EXT)

                # Copy the palette file to our PAC source directory.
                shutil.copyfile(hpl_src_path, hpl_dst_path)

            try:
                create_pac(temp_dir, self.pac_path)

            except Exception:
                raise WorkThreadException("Error Creating PAC File", f"Failed to create PAC file from HPL file list!")
