import io
import os
import json

from libhip import HIPImage
from libhpl import PNGPaletteImage
from libscr.commands import CMD_MOVE_REGISTER, CMD_MOVE_END_REGISTER, CMD_MOVE_INPUT
from libscr.symbols import MOVE_TYPE_SPECIAL, MOVE_TYPE_DISTORTION, MOVE_TYPE_ASTRAL
from libscr.scr import get_normal_input_str, get_special_input_str

from .work_thread import WorkThread, AppError, AppException

SCR_FILE_FMT = "scr_{}.json"
NOT_APPLICABLE_STR = "N/A"
NOT_APPLICABLE_NUM = -1


class AnimationPrepThread(WorkThread):
    def __init__(self, character, animation_name, paths, palette_full_path, frame_files):
        WorkThread.__init__(self)
        self.palette_full_path = palette_full_path
        self.animation_name = animation_name
        self.frame_files = frame_files
        self.character = character
        self.paths = paths
        self.move_input = NOT_APPLICABLE_STR
        self.move_startup = NOT_APPLICABLE_NUM
        self.move_active = NOT_APPLICABLE_NUM
        self.move_recovery = NOT_APPLICABLE_NUM
        self.sprites = []
        self.hitboxes = []
        self.hurtboxes = []

    def _load_image_data(self, src_chunks, hip_full_path, sprite_duration):
        """
        Load sprite image data for the animation into memory.
        We get the image data for each chunk defined by the script data.
        We save the image as a PNG, so it is ready for display in the
        dialog, as well as the position and layer for each chunk.
        """
        hip_file = os.path.basename(hip_full_path)
        chunks = []

        try:
            hip_image = HIPImage()
            hip_image.load_hip(hip_full_path)

        except Exception:
            raise AppException("Error Extracting Sprite", f"Failed to extract PNG image from {hip_file}!")

        for chunk in src_chunks:
            chunk_pos, chunk_layer, chunk_png = hip_image.get_chunk(**chunk)
            chunk_bytes = io.BytesIO()

            try:
                png_image = PNGPaletteImage()
                png_image.load_png(chunk_png)
                png_image.load_hpl(self.palette_full_path)
                png_image.save_png(chunk_bytes)

            except Exception:
                message = f"Failed to set HPL palette ({self.palette_full_path}) on sprite!"
                raise AppException("Error Modifying Sprite", message)

            chunks.append((chunk_pos, chunk_layer, chunk_bytes.getvalue()))

        self.sprites.append((sprite_duration, hip_image.coord_size, chunks))

    def _load_sprite(self, hip_full_path, collision_cache_path, sprite_duration):
        """
        Load sprite image and collision box data into memory.
        The collision boxes simply require us to read a JSON file and retain some data from those objects.
        The image data is more complex and is handled in another method.
        """
        collision_file = os.path.basename(hip_full_path).replace(".hip", ".json")
        collision_full_path = os.path.join(collision_cache_path, collision_file)

        with open(collision_full_path, "r") as col_fp:
            collision_data = json.load(col_fp)

        self.hitboxes.append(collision_data["hitboxes"])
        self.hurtboxes.append(collision_data["hurtboxes"])

        self._load_image_data(collision_data["chunks"], hip_full_path, sprite_duration)

    def _get_move(self):
        """
        Look for a registered move with the same name as our animation.
        Return the script data associated to that move if it exists.
        """
        script_cache_path = self.paths.get_script_cache_path(self.character)
        script_path = os.path.join(script_cache_path, SCR_FILE_FMT.format(self.character))

        with open(script_path, "r") as ast_fp:
            nodes = json.load(ast_fp)

        for node in nodes:
            within_move = False
            move_data = []

            for nested_node in node["body"]:
                cmd_id = nested_node["cmd_id"]

                if cmd_id == CMD_MOVE_REGISTER:
                    if nested_node["cmd_args"][0] == self.animation_name:
                        move_data.append(nested_node)
                        within_move = True

                elif cmd_id == CMD_MOVE_END_REGISTER and within_move:
                    return move_data

                elif within_move:
                    move_data.append(nested_node)

        return []

    def _get_input(self):
        """
        Get the input for the move associated to our animation.
        If there is no move data then we assume this animation is not the result of player input.
        If there is move data then we get a human-readable string representation of the
        player input required for the move to be performed.
        """
        move_data = self._get_move()

        if move_data:
            move_input_value = move_data[0]["cmd_args"][1]

            if move_input_value in (MOVE_TYPE_SPECIAL, MOVE_TYPE_DISTORTION, MOVE_TYPE_ASTRAL):
                motion_value = None
                button_value = None

                for node in move_data:
                    if node["cmd_id"] == CMD_MOVE_INPUT:
                        if motion_value is None:
                            motion_value = node["cmd_args"][0]

                        else:
                            button_value = node["cmd_args"][0]
                            break

                if motion_value is None:
                    raise AppError("Move Fetch Error", "Did not find the move input motion value!")

                if button_value is None:
                    raise AppError("Move Fetch Error", "Did not find the move input button value!")

                self.move_input = get_special_input_str(motion_value, button_value)

            else:
                self.move_input = get_normal_input_str(move_input_value)

    def _get_frame_data(self):
        """
        Calculate the frame data that pertains to this animation.
        If this animation is not an animation associated to a player input then we skip
        frame data calculation.
        FIXME: This math is incorrect for moves that can be held.
        """
        # If we don't have an input then how would there be frame data?
        if self.move_input == NOT_APPLICABLE_STR:
            return

        index = 0
        # Our calculation for startup seems to be always off-by-one when compared to dustloop.
        startup = 1
        # TODO: Seen more than once, compared to dustloop the active time is 2 frames shorter and recovery
        #       is 2 frames longer. Is this a real issue or is dustloop somehow wrong? I have my doubts about
        #       dustloop being incorrect but it is within the realm of possibility.
        active = 0
        recovery = 0

        for hitboxes, hurtboxes in zip(self.hitboxes, self.hurtboxes):
            sprite_duration = self.sprites[index][0]

            if not hitboxes and active <= 0:
                startup += sprite_duration

            # FIXME: This does not take into account moves that hit multiple times separately (e.g. Amane 5A).
            if hitboxes:
                active += sprite_duration

            if not hitboxes and active > 0:
                recovery += sprite_duration

            index += 1

        self.move_startup = startup
        self.move_active = active
        self.move_recovery = recovery

    def work(self):
        collision_cache_path = self.paths.get_collision_cache_path(self.character)

        for hip_full_path, sprite_duration in self.frame_files:
            self._load_sprite(hip_full_path, collision_cache_path, sprite_duration)

        self._get_input()
        self._get_frame_data()
