import io
import os
import json

from libhip import HIPImage
from libhpl import PNGPaletteImage

from .work_thread import WorkThread, AppException


class AnimationPrepThread(WorkThread):
    def __init__(self, character, paths, palette_full_path, frame_files):
        WorkThread.__init__(self)
        self.palette_full_path = palette_full_path
        self.frame_files = frame_files
        self.character = character
        self.paths = paths
        self.frames = []
        self.chunks = []
        self.hitboxes = []
        self.hurtboxes = []

    def _load_frames(self):
        """
        Load sprite data for the animation into memory.
        """
        for hip_full_path in self.frame_files:
            hip_file = os.path.basename(hip_full_path)
            frame_count = 1  # FIXME: this value has to come from script data!

            png_bytes = io.BytesIO()
            frame_bytes = io.BytesIO()

            try:
                hip_image = HIPImage()
                hip_image.load_hip(hip_full_path)
                hip_image.save_png(png_bytes)
                png_bytes.seek(0)

            except Exception:
                raise AppException("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")

            try:
                png_image = PNGPaletteImage()
                png_image.load_png(png_bytes)
                png_image.load_hpl(self.palette_full_path)
                png_image.save_png(frame_bytes)

            except Exception:
                message = f"Failed to set HPL palette ({self.palette_full_path}) on HIP image {hip_file}!"
                raise AppException("Error Modifying Image", message)

            self.frames.append((frame_count, hip_image.coord_size, hip_image.offset, frame_bytes.getvalue()))

    def _load_collisions(self):
        """
        Load collision box data into memory.
        """
        collision_cache_path = self.paths.get_collision_cache_path(self.character)

        for frame_full_path in self.frame_files:
            collision_file = os.path.basename(frame_full_path).replace(".hip", ".json")
            collision_full_path = os.path.join(collision_cache_path, collision_file)

            with open(collision_full_path, "r") as col_fp:
                collision_data = json.load(col_fp)

            self.chunks.append(collision_data["chunks"])
            self.hitboxes.append(collision_data["hitboxes"])
            self.hurtboxes.append(collision_data["hurtboxes"])

    def work(self):
        self._load_frames()
        self._load_collisions()
