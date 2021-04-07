import os
import shutil
import tempfile

from PyQt5 import QtCore

from libpac import create_pac

from .util import *


class ApplyThread(QtCore.QThread):

    message = QtCore.pyqtSignal(str)

    def __init__(self, bbcf_install, files_to_apply):
        QtCore.QThread.__init__(self)
        self.files_to_apply = files_to_apply
        self.bbcf_install = bbcf_install

    def run(self):
        bbcf_game_data_dir = os.path.join(self.bbcf_install, "data", "Char")

        for pac_file_name, hpl_file_list in self.files_to_apply.items():
            pac_full_path = os.path.join(bbcf_game_data_dir, pac_file_name)
            temp_dir = tempfile.mkdtemp()

            self.message.emit("Gathering HPL palette files...")
            for hpl_full_path in hpl_file_list:
                if hpl_full_path.endswith(DIRTY_PALETTE_EXT):
                    updated_full_path = hpl_full_path.replace(DIRTY_PALETTE_EXT, PALETTE_EXT)
                    base_name = os.path.basename(updated_full_path)

                    temp_full_path = os.path.join(temp_dir, base_name)
                    shutil.copyfile(hpl_full_path, temp_full_path)

                    os.remove(updated_full_path)
                    shutil.copyfile(hpl_full_path, updated_full_path)
                    os.remove(hpl_full_path)

                else:
                    temp_full_path = os.path.join(temp_dir, os.path.basename(hpl_full_path))
                    shutil.copyfile(hpl_full_path, temp_full_path)

            self.message.emit(f"Creating {pac_file_name}...")
            create_pac(temp_dir, pac_full_path)
            shutil.rmtree(temp_dir)