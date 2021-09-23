from PyQt5 import Qt, QtCore, QtWidgets

from .util import block_signals
from .ui.animation_dialog_ui import Ui_Dialog

# A single "frame" as a time duration (in milliseconds).
# Note that fighting games run at 60 FPS, and a single frame is the standard unit of time for these games.
FRAME_TIME = 1.0 / 60.0 * 1000.0

# The first chunk is actually an offset into the sprite coordinate system.
# The second chunk defines a box around the character eyes.
# The third chunk defines a box around the character mouth.
CHUNK_OFFSET = 0
CHUNK_EYES = 1
CHUNK_MOUTH = 2


class AnimationDialog(QtWidgets.QDialog):
    def __init__(self, anim_prep, parent=None):
        QtWidgets.QDialog.__init__(self, parent, flags=QtCore.Qt.WindowType.WindowTitleHint)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Animation Details")

        self.num_frames = len(anim_prep.frames)
        self.frames = anim_prep.frames
        self.chunks = anim_prep.chunks
        self.hitboxes = anim_prep.hitboxes
        self.hurtboxes = anim_prep.hurtboxes
        self.playing = False
        self.index = 0

        # Set up UI controls and relevant signals.
        self.ui.play_button.clicked.connect(self.play)
        self.ui.pause_button.clicked.connect(self.pause)
        self.ui.stop_button.clicked.connect(self.stop)
        self.ui.show_boxes.stateChanged.connect(self._update_frame)
        self.ui.frame_slider.keyPressEvent = self.keyPressEvent
        self.ui.frame_slider.valueChanged.connect(self._slider_changed)
        self.ui.frame_slider.setMaximum(self.num_frames - 1)
        self.ui.frame_slider.setPageStep(1)

        # Set up initial frame-data line edits.
        self.ui.input_edit.setText(anim_prep.move_input)
        self.ui.startup_edit.setValue(anim_prep.move_startup)
        self.ui.active_edit.setValue(anim_prep.move_active)
        self.ui.recovery_edit.setValue(anim_prep.move_recovery)

        # Set up our sprite viewer with a scene.
        # A scene can load a pixmap (i.e. an image like a PNG) from file or bytestring and display it.
        self.sprite_scene = QtWidgets.QGraphicsScene()
        self.ui.animation_view.setScene(self.sprite_scene)
        self.sprite_pixmap = None

        self._update_frame()

    def keyPressEvent(self, evt):
        """
        Sliders are frequently able to be changed via page up and page down buttons.
        Allow for doing this regardless of the focused widget in the dialog.
        """
        if not self.playing and evt.key() == QtCore.Qt.Key.Key_PageUp:
            self._update_index(1)
            self._update_frame()

        if not self.playing and evt.key() == QtCore.Qt.Key.Key_PageDown:
            self._update_index(-1)
            self._update_frame()

    def _slider_changed(self, index):
        """
        Update the index and current displayed frame when the user drags the slider.
        """
        self.index = index
        self._update_frame()

    def play(self):
        """
        Play the full animation.
        """
        if not self.playing:
            self.playing = True
            self._update_frame()
            self._ui_enables(False)

    def pause(self):
        """
        Stop the play procedure without resetting the current index.
        """
        self.playing = False
        self._ui_enables(True)

    def stop(self):
        """
        Stop the play procedure and reset the index to the start of the animation.
        """
        self.playing = False
        self.index = 0
        self.ui.frame_slider.setSliderPosition(0)
        self._update_frame()
        self._ui_enables(True)

    def _ui_enables(self, state):
        """
        Set the state of UI elements that need to be disabled while an animation is playing.
        """
        self.ui.loop_animation.setEnabled(state)
        self.ui.show_effects.setEnabled(state)
        self.ui.show_boxes.setEnabled(state)
        self.ui.frame_slider.setEnabled(state)

    def _update_index(self, value):
        """
        Update the current frame index.
        The value can be moved "forward" or "backward" through the frame list.
        """
        if value not in (-1, 1):
            raise ValueError("Can only change the frame index by -1 or 1!")

        self.index += value

        # Our min value is 0.
        # If the index is less than that we need to wrap around to the max value.
        if self.index < 0:
            self.index = self.num_frames - 1

        # Likewise, our max value is `self.num_frames - 1`.
        # If the index is more than that we need to wrap around to the min value.
        elif self.index >= self.num_frames:
            self.index = 0

        # We do not want the slider to emit signals here as `_update_index` is sometimes
        # invoked from `_update_frame`. The value changed handler for the slider also invokes `_update_frame`.
        # If we allow the slider to emit signals here it would cause infinite recursion.
        with block_signals(self.ui.frame_slider):
            self.ui.frame_slider.setSliderPosition(self.index)

    def _make_rect_item(self, x, y, width, height, color, **_):
        """
        Create a `QGraphicsRectItem` to represent a collision box.
        This is used for displaying hitboxes and hurtboxes.
        Helper mostly exists so we can use the **kwargs syntax to pass
        our game data parameters without having to care about popping out
        data that is not pertinent to this item.
        """
        chunk = self.chunks[self.index][CHUNK_OFFSET]

        x -= chunk["x"]
        y -= chunk["y"]

        rect_item = QtWidgets.QGraphicsRectItem(x, y, width, height)
        rect_item.setPen(Qt.QPen(color))

        return rect_item

    def _update_frame(self, *_, **__):
        """
        Clear our graphics view and update it with the next frame of our animation.

        Reference: https://github.com/Labreezy/bb-collision-editor/blob/master/BBCollisionEditor/OverlaidImage.cs
        """
        # Clear our image data.
        self.sprite_scene.clear()

        # The number of frames (i.e. units of time) and binary image data for the animation.
        sprite_duration, coord_size, offset, frame_bytes = self.frames[self.index]
        hitboxes = self.hitboxes[self.index]
        hurtboxes = self.hurtboxes[self.index]

        self.sprite_pixmap = Qt.QPixmap()
        self.sprite_pixmap.loadFromData(frame_bytes, "PNG")

        # Add a transparent rectangle.
        rect_item = QtWidgets.QGraphicsRectItem(0, 0, *coord_size)
        rect_item.setPen(Qt.QPen(Qt.QColorConstants.Transparent))
        self.sprite_scene.addItem(rect_item)

        # Add our animation frame to the scene and set its position from the HIP meta data.
        pixmap_item = self.sprite_scene.addPixmap(self.sprite_pixmap)
        pixmap_item.setPos(*offset)

        # If our Hit/Hurt box checkbox is ticked we should display that information.
        if self.ui.show_boxes.checkState() == QtCore.Qt.CheckState.Checked:
            for hitbox in hitboxes:
                rect_item = self._make_rect_item(color=Qt.QColorConstants.Red, **hitbox)
                self.sprite_scene.addItem(rect_item)

            for hurtbox in hurtboxes:
                rect_item = self._make_rect_item(color=Qt.QColorConstants.Blue, **hurtbox)
                self.sprite_scene.addItem(rect_item)

        # Ensure the graphics view is refreshed so our changes are visible to the user.
        self.ui.animation_view.viewport().update()

        # If our animation is playing then we need to update our index and check if we should
        # not schedule a render of the next frame in the animation.
        if self.playing:
            self._update_index(1)

            # If our index, after update, is 0 then we have completed an animation loop.
            # Only continue looping if the loop checkbox is ticked.
            if self.index == 0 and self.ui.loop_animation.checkState() == QtCore.Qt.CheckState.Unchecked:
                self.stop()

            # If we are indeed looping and have not stopped the play routine then we should schedule
            # the next frame render. The delay between animation frames is determined by the game data.
            if self.playing:
                QtCore.QTimer.singleShot(sprite_duration * FRAME_TIME, self._update_frame)
