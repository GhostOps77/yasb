import logging
import re
import subprocess

from PyQt6.QtCore import QEvent, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget

from core.event_enums import KomorebiEvent
from core.event_service import EventService
from core.utils.utilities import PopupWidget, build_widget_label
from core.utils.widgets.komorebi.client import KomorebiClient
from core.validation.widgets.komorebi.control import VALIDATION_SCHEMA
from core.widgets.base import BaseHBoxLayout, BaseVBoxLayout, BaseWidget, BaseYasbWidgetLabel

try:
    from core.utils.widgets.komorebi.event_listener import KomorebiEventListener
except ImportError:
    KomorebiEventListener = None
    logging.warning("Failed to load Komorebi Event Listener")


class ExtPopupWidget(PopupWidget):
    def eventFilter(self, obj, event):
        parent = self.parent()
        # When menu is locked, block usually hiding events from komorebi
        if isinstance(parent, KomorebiControlWidget) and parent._lock_menu:
            if event.type() == QEvent.Type.Close:
                return True
        return super().eventFilter(obj, event)


class KomorebiControlWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    k_signal_connect = pyqtSignal(dict)
    k_signal_disconnect = pyqtSignal()
    event_listener = KomorebiEventListener

    def __init__(
        self,
        label: str,
        icons: dict[str, str],
        run_ahk: bool,
        run_whkd: bool,
        config_path: str | None,
        show_version: bool,
        komorebi_menu: dict[str, str],
        animation: dict[str, str],
        **kwargs,
    ):
        super().__init__(class_name="komorebi-control-widget", **kwargs)

        self._label_content = label
        self._icons = icons
        self._run_ahk = run_ahk
        self._run_whkd = run_whkd
        self._config_path = config_path
        self._show_version = show_version
        self._komorebi_menu = komorebi_menu
        self._animation = animation
        self._is_komorebi_connected = False
        self._locked_ui = False
        self._lock_menu = False
        self._version_text = None

        # Initialize the event service
        self._event_service = EventService()
        self._komorebic = KomorebiClient()

        build_widget_label(self, self._label_content)

        self.register_callback("toggle_menu", self._toggle_menu)

        # Register events
        self._register_signals_and_events()

    def _register_signals_and_events(self):
        # Connect signals to handlers
        self.k_signal_connect.connect(self._on_komorebi_connect_event)
        self.k_signal_disconnect.connect(self._on_komorebi_disconnect_event)
        # Register for events
        self._event_service.register_event(KomorebiEvent.KomorebiConnect, self.k_signal_connect)
        self._event_service.register_event(KomorebiEvent.KomorebiDisconnect, self.k_signal_disconnect)
        # Ensure we unregister on destruction to prevent late emits hitting deleted objects
        try:
            self.destroyed.connect(self._on_destroyed)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _on_destroyed(self, *args):
        try:
            self._event_service.unregister_event(KomorebiEvent.KomorebiConnect, self.k_signal_connect)
            self._event_service.unregister_event(KomorebiEvent.KomorebiDisconnect, self.k_signal_disconnect)
        except Exception:
            pass

    def _start_version_check(self):
        """Starts a background thread to retrieve the Komorebi version."""
        self._version_thread = VersionCheckThread(self._komorebic)
        self._version_thread.version_result.connect(self._on_version_result)
        self._version_thread.start()

    def _on_version_result(self, version):
        """Receives the Komorebi version from the thread and updates the UI."""
        self._version_text = f"komorebi v{version}" if version else None
        if getattr(self, "dialog", None) and self.dialog.isVisible():
            self._update_menu_button_states()
            # Update the version label in the currently open dialog
            for child in self.dialog.findChildren(QLabel):
                if child.property("class") == "text version":
                    child.setText(self._version_text)
                    break

        # Also update stored label if we created it on the dialog
        if hasattr(self, "_version_label") and self._show_version:
            self._version_label.setText(self._version_text if self._version_text else "")

    def _toggle_menu(self):
        self._animate()
        self.show_menu()

    def show_menu(self):
        # If we don't have a version yet, start an async check
        if self._version_text is None:
            self._start_version_check()

        # Build the popup dialog
        self.dialog = ExtPopupWidget(
            self,
            self._komorebi_menu["blur"],
            self._komorebi_menu["round_corners"],
            self._komorebi_menu["round_corners_type"],
            self._komorebi_menu["border_color"],
        )
        self.dialog.setProperty("class", "komorebi-control-menu")

        layout = BaseVBoxLayout()

        # Top row with buttons
        buttons_row = QWidget()
        buttons_layout = BaseHBoxLayout(buttons_row, spacing=5, paddings=10)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Store buttons as class attributes so we can update them
        self.start_btn = BaseYasbWidgetLabel(self._icons["start"])
        self.stop_btn = BaseYasbWidgetLabel(self._icons["stop"])
        self.reload_btn = BaseYasbWidgetLabel(self._icons["reload"])

        # Connect button click events
        self.start_btn.mousePressEvent = lambda e: self._start_komorebi()
        self.stop_btn.mousePressEvent = lambda e: self._stop_komorebi()
        self.reload_btn.mousePressEvent = lambda e: self._reload_komorebi()

        # Update the button states based on current connection status
        self._update_menu_button_states()

        buttons_layout.addWidgets(self.start_btn, self.stop_btn, self.reload_btn)

        # Bottom row with version info
        version_row = QWidget()
        version_row.setProperty("class", "footer")

        version_layout = BaseVBoxLayout(version_row)
        version_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Keep the version label as an instance attribute so we can update it later
        self._version_label = QLabel(self._version_text)
        self._version_label.setProperty("class", "text version")
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._version_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        version_layout.addWidget(self._version_label)

        # Add widgets to main layout vertically
        layout.addWidget(buttons_row)
        if self._show_version:
            layout.addWidget(version_row)

        self.dialog.setLayout(layout)

        self.dialog.adjustSize()
        self.dialog.setPosition(
            alignment=self._komorebi_menu["alignment"],
            direction=self._komorebi_menu["direction"],
            offset_left=self._komorebi_menu["offset_left"],
            offset_top=self._komorebi_menu["offset_top"],
        )

        self.dialog.show()

    def _on_komorebi_connect_event(self) -> None:
        self._is_komorebi_connected = True
        self._locked_ui = False
        # Clear the reloading flag if it exists
        if hasattr(self, "_is_reloading"):
            self._is_reloading = False

        try:
            self._update_menu_button_states()
        except:
            pass

        if hasattr(self, "_version_label"):
            try:
                self._version_label.setText(self._version_text if self._version_text else "")
            except Exception:
                pass

        self._lock_menu = False
        # If the dialog is visible (and was locked before), force it to regain focus.
        try:
            if hasattr(self, "dialog") and self.dialog is not None and self.dialog.isVisible():
                self.dialog.activateWindow()
                self.dialog.setFocus()
        except RuntimeError:
            # The dialog has already been deleted.
            self.dialog = None

    def _on_komorebi_disconnect_event(self) -> None:
        self._is_komorebi_connected = False
        # Only unlock UI if this isn't part of a reload operation
        if not hasattr(self, "_is_reloading") or not self._is_reloading:
            self._locked_ui = False

        try:
            self._update_menu_button_states()
        except:
            pass  # Dialog may have been deleted

    def _update_menu_button_states(self):
        # Check if buttons should be disabled
        disable_buttons = self._locked_ui or self._version_text is None

        self.start_btn.setDisabled(disable_buttons)
        self.stop_btn.setDisabled(disable_buttons)
        self.reload_btn.setDisabled(disable_buttons)

        # Update the button classes
        if self._is_komorebi_connected:
            self.start_btn.setProperty("class", "button start")
            self.stop_btn.setProperty("class", "button stop active")
            self.reload_btn.setProperty("class", "button reload active")
        else:
            self.start_btn.setProperty("class", "button start active")
            self.stop_btn.setProperty("class", "button stop")
            self.reload_btn.setProperty("class", "button reload")

        # Force style refresh on each button
        for btn in (self.start_btn, self.stop_btn, self.reload_btn):
            style = btn.style()
            style.unpolish(btn)
            style.polish(btn)

    def _run_komorebi_command(self, command: str):
        """Runs a Komorebi command with locked UI and error handling."""
        self._locked_ui = True
        self._update_menu_button_states()
        try:
            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            self._locked_ui = False
            logging.error(f"Error running '{command}': {e}")

    def _build_komorebi_flags(self, include_config: bool = True) -> str:
        """Build command line flags based on configuration."""
        flags = []
        if self._run_whkd:
            flags.append("--whkd")
        if self._run_ahk:
            flags.append("--ahk")
        if include_config and self._config_path:
            flags.append(f"--config={self._config_path}")
        return " ".join(flags)

    def _start_komorebi(self):
        self._lock_menu = True
        if not self._is_komorebi_connected:
            flags = self._build_komorebi_flags(include_config=True)
            command = f"{self._komorebic._komorebic_path} start {flags}"
            # If the menu is open, show a transient starting message
            if hasattr(self, "_version_label") and getattr(self, "dialog", None) and self.dialog.isVisible():
                try:
                    self._version_label.setText("Starting...")
                except Exception:
                    pass
            self._run_komorebi_command(command)

    def _stop_komorebi(self):
        if self._is_komorebi_connected:
            # Build flags for stop without including the --config option
            stop_flags = self._build_komorebi_flags(include_config=False)
            command = f"{self._komorebic._komorebic_path} stop {stop_flags}"
            self._run_komorebi_command(command)

    def _reload_komorebi(self):
        self._lock_menu = True
        if self._is_komorebi_connected:
            self._is_reloading = True
            stop_flags = self._build_komorebi_flags(include_config=False)
            start_flags = self._build_komorebi_flags(include_config=True)
            command = (
                f"{self._komorebic._komorebic_path} stop {stop_flags} && "
                f" {self._komorebic._komorebic_path} start {start_flags}"
            )

            if hasattr(self, "_version_label") and getattr(self, "dialog", None) and self.dialog.isVisible():
                try:
                    self._version_label.setText("Reloading...")
                except Exception:
                    pass
            try:
                self._run_komorebi_command(command)
            except Exception as e:
                self._is_reloading = False
                self._locked_ui = False
                logging.error(f"Error reloading Komorebi: {e}")


class VersionCheckThread(QThread):
    version_result = pyqtSignal(str)

    def __init__(self, komorebic_client):
        super().__init__()
        self._komorebic = komorebic_client

    def run(self):
        version = self.get_version()
        self.version_result.emit(version if version else None)

    def get_version(self) -> str | None:
        """Returns the Komorebi version or None if unavailable."""
        try:
            output = subprocess.check_output(
                [self._komorebic._komorebic_path, "--version"],
                timeout=self._komorebic._timeout_secs,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
            )
            match = re.search(r"komorebic\s+(\d+\.\d+\.\d+)", output.strip().split("\n")[0])
            return match.group(1) if match else None
        except:
            return None
