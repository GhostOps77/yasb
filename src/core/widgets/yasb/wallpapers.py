import ctypes
import logging
import os
import random
import subprocess
import threading

import pythoncom
import pywintypes
import win32gui
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from win32comext.shell import shell, shellcon

from core.event_service import EventService
from core.utils.alert_dialog import raise_info_alert
from core.utils.tooltip import set_tooltip
from core.utils.utilities import iterate_label_as_parts
from core.utils.widgets.animation_manager import AnimationManager
from core.utils.widgets.wallpapers.wallpapers_gallery import ImageGallery
from core.utils.win32.utilities import get_foreground_hwnd, set_foreground_hwnd
from core.validation.widgets.yasb.wallpapers import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget
from settings import DEBUG


class WallpapersWidget(BaseWidget):
    set_wallpaper_signal = pyqtSignal(str)
    handle_widget_cli = pyqtSignal(str, str)

    user32 = ctypes.windll.user32
    validation_schema = VALIDATION_SCHEMA
    # Shared state for all Wallpaper instances
    _shared_timer_running = False

    def __init__(
        self,
        label: str,
        update_interval: int,
        change_automatically: bool,
        image_path: str,
        tooltip: bool,
        animation: dict[str, str],
        run_after: list[str],
        gallery: dict = None,
        **kwargs,
    ):
        """Initialize the WallpapersWidget with configuration parameters."""
        super().__init__(int(update_interval * 1000), class_name="wallpapers-widget", **kwargs)
        self._image_gallery = None

        self._event_service = EventService()
        self._label_content = label
        self._change_automatically = change_automatically
        self._image_path = image_path
        self._tooltip = tooltip
        self._run_after = run_after
        self._gallery = gallery
        self._animation = animation

        self._last_image = None
        self._is_running = False
        self._popup_from_cli = False

        self._create_dynamically_label(self._label_content)

        self.set_wallpaper_signal.connect(self.change_background)
        self._event_service.register_event("set_wallpaper_signal", self.set_wallpaper_signal)

        self.register_callback("change_background", self.change_background)
        self.register_callback("timer", self.change_background)

        if self._change_automatically:
            self.start_timer()

        self._previous_hwnd = None
        self.handle_widget_cli.connect(self._handle_widget_cli)
        self._event_service.register_event("handle_widget_cli", self.handle_widget_cli)

    def _handle_widget_cli(self, widget: str, screen: str):
        """Handle widget CLI commands"""
        if widget != "wallpapers":
            return

        current_screen = self.window().screen() if self.window() else None
        current_screen_name = current_screen.name() if current_screen else None
        if not screen or (current_screen_name and screen.lower() == current_screen_name.lower()):
            self._popup_from_cli = True
            self._toggle_widget()

    def _toggle_widget(self):
        """Toggle the visibility of the widget."""

        if self._image_gallery is not None and self._image_gallery.isVisible():
            self._image_gallery.fade_out_and_close_gallery()
            if self._previous_hwnd:
                set_foreground_hwnd(self._previous_hwnd)
                self._previous_hwnd = None
        else:
            if getattr(self, "_popup_from_cli", False):
                self._previous_hwnd = get_foreground_hwnd()
                self._popup_from_cli = False

            self._image_gallery = ImageGallery(self._image_path, self._gallery)
            self._image_gallery.fade_in_gallery(parent=self)

    def start_timer(self):
        """Start the timer for automatic wallpaper changes."""
        if not WallpapersWidget._shared_timer_running:
            if self.timer_interval and self.timer_interval > 0:
                self.timer.timeout.connect(self._timer_callback)
                self.timer.start(self.timer_interval)
                WallpapersWidget._shared_timer_running = True

    def _create_dynamically_label(self, content: str):
        """Create labels dynamically based on the provided content."""

        def process_content(content, is_alt=False):
            widgets = []
            for label in iterate_label_as_parts(self, widgets, content):
                label.mousePressEvent = self.handle_mouse_events
                if self._tooltip:
                    set_tooltip(label, "Change Wallpaper")

            return widgets

        self._widgets = process_content(content)

    def _update_label(self):
        """Update the label content dynamically."""

        active_widgets = self._widgets
        active_label_content = self._label_content

        for _ in iterate_label_as_parts(self, active_widgets, active_label_content):
            pass

    def _make_filter(self, class_name: str, title: str):
        """
        Create a filter function for enumerating windows.
        https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows
        """

        def enum_windows(handle: int, h_list: list):
            if not (class_name or title):
                h_list.append(handle)
            if class_name and class_name not in win32gui.GetClassName(handle):
                return True  # continue enumeration
            if title and title not in win32gui.GetWindowText(handle):
                return True  # continue enumeration
            h_list.append(handle)

        return enum_windows

    def find_window_handles(self, parent: int = None, window_class: str = None, title: str = None) -> list[int]:
        """Find window handles based on class name and title."""
        cb = self._make_filter(window_class, title)
        try:
            handle_list = []
            if parent:
                win32gui.EnumChildWindows(parent, cb, handle_list)
            else:
                win32gui.EnumWindows(cb, handle_list)
            return handle_list
        except pywintypes.error:
            return []

    def force_refresh(self):
        """Force a system refresh of user parameters."""
        self.user32.UpdatePerUserSystemParameters(1)

    def enable_activedesktop(self):
        """Enable the Active Desktop feature."""
        try:
            progman = self.find_window_handles(window_class="Progman")[0]
            cryptic_params = (0x52C, 0, 0, 0, 500, None)
            self.user32.SendMessageTimeoutW(progman, *cryptic_params)
        except IndexError as e:
            logging.error("Cannot enable Active Desktop: %s", e)
            raise OSError("Cannot enable Active Desktop") from e

    def set_wallpaper(self, image_path: str, use_activedesktop: bool = True):
        """Set the desktop wallpaper to the specified image."""
        if use_activedesktop:
            self.enable_activedesktop()

        pythoncom.CoInitialize()
        iad = pythoncom.CoCreateInstance(
            shell.CLSID_ActiveDesktop,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IActiveDesktop,
        )
        iad.SetWallpaper(str(image_path), 0)
        iad.ApplyChanges(shellcon.AD_APPLY_ALL)
        self.force_refresh()

    def handle_mouse_events(self, event=None):
        """Handle mouse events for changing wallpapers."""

        if not os.path.exists(self._image_path):
            raise_info_alert(
                title="Error",
                msg=f"The specified directory does not exist\n{self._image_path}",
                informative_msg="Please check the path and set a valid directory in the configuration.",
                rich_text=True,
            )
            return

        if not self._gallery["enabled"]:
            if event is None or event.button() == Qt.MouseButton.LeftButton:
                self.change_background()
            return

        if self._animation["enabled"]:
            AnimationManager.animate(self, self._animation["type"], self._animation["duration"])

        if event is None or event.button() == Qt.MouseButton.LeftButton:
            if self._image_gallery is not None and self._image_gallery.isVisible():
                self._image_gallery.fade_out_and_close_gallery()
            else:
                self._image_gallery = ImageGallery(self._image_path, self._gallery)
                self._image_gallery.fade_in_gallery(parent=self)

        if event is None or event.button() == Qt.MouseButton.RightButton:
            self.change_background()

    def change_background(self, image_path: str = None):
        """Change the desktop wallpaper to a new image."""
        if self._is_running:
            return

        if self._run_after:
            self._is_running = True
            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(0.5)
            self._widget_container.setGraphicsEffect(opacity_effect)

        wallpapers = [
            os.path.join(self._image_path, f)
            for f in os.listdir(self._image_path)
            if f.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))
        ]

        if image_path:
            new_wallpaper = image_path
        else:
            """Randomly select a new wallpaper and prevent the same wallpaper from being selected"""
            new_wallpaper = random.choice(wallpapers)
            while new_wallpaper == self._last_image and len(wallpapers) > 1:
                new_wallpaper = random.choice(wallpapers)

        try:
            self.set_wallpaper(new_wallpaper)
            self._last_image = new_wallpaper
        except Exception as e:
            logging.error(f"Error setting wallpaper {new_wallpaper}: {e}")

        if self._run_after:
            threading.Thread(target=self.run_after_command, args=(new_wallpaper,)).start()

    def run_after_command(self, new_wallpaper):
        """Run post-change commands after setting the wallpaper."""
        if self._run_after:
            for command in self._run_after:
                formatted_command = command.format(image=f'"{new_wallpaper}"')
                if DEBUG:
                    logging.debug(f"Running command: {formatted_command}")
                result = subprocess.run(formatted_command, shell=True, capture_output=True, text=True)
                if result.stderr:
                    logging.error(f"error: {result.stderr}")

        reset_effect = QGraphicsOpacityEffect()
        reset_effect.setOpacity(1.0)
        self._widget_container.setGraphicsEffect(reset_effect)
        self._is_running = False
