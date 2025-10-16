import logging

from PyQt6.QtCore import pyqtSignal

from core.event_service import EventService
from core.utils.utilities import build_widget_label, is_windows_10, iterate_label_as_parts
from core.utils.win32.system_function import notification_center, quick_settings
from core.validation.widgets.yasb.notifications import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget

try:
    from core.utils.widgets.notifications.windows_notification import WindowsNotificationEventListener
except ImportError:
    WindowsNotificationEventListener = None
    logging.warning("Failed to load Windows Notification Event Listener")


class NotificationsWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA
    windows_notification_update_signal = pyqtSignal(int)
    event_listener = WindowsNotificationEventListener

    def __init__(
        self,
        label: str,
        label_alt: str,
        class_name: str,
        hide_empty: bool,
        tooltip: bool,
        icons: dict,
        animation: dict[str, str],
        callbacks: dict[str, str],
        **kwargs,
    ):
        super().__init__(class_name=f"notification-widget {class_name}", **kwargs)
        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt
        self._notification_count = 0

        self._hide_empty = hide_empty
        self._tooltip = tooltip
        self._icons = icons
        self._animation = animation
        self._callbacks = callbacks

        build_widget_label(self, self._label_content, self._label_alt_content, self._label_shadow)

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("toggle_notification", self._toggle_notification)
        self.register_callback("clear_notifications", self._clear_notifications)
        self.map_callbacks(callbacks)

        # Register the WindowsNotificationUpdate event
        self.event_service = EventService()
        self.event_service.register_event("WindowsNotificationUpdate", self.windows_notification_update_signal)
        self.windows_notification_update_signal.connect(self._on_windows_notification_update)

        self._update_label()

    def _on_windows_notification_update(self, total_notifications):
        self._notification_count = total_notifications
        if total_notifications > 0:
            self.setVisible(True)
        elif self._hide_empty:
            self.setVisible(False)
        self._update_label()

    def _toggle_notification(self):
        self._animate()
        if is_windows_10():
            quick_settings()
        else:
            notification_center()

    def _toggle_label(self):
        self._animate()
        self._show_alt_label = not self._show_alt_label
        # for widget in self._widgets:
        #     widget.setVisible(not self._show_alt_label)
        # for widget in self._widgets_alt:
        #     widget.setVisible(self._show_alt_label)
        self._update_label()

    def _clear_notifications(self):
        self._animate()
        if WindowsNotificationEventListener:
            self.event_service.emit_event("WindowsNotificationClear", "clear_all_notifications")

    def _update_label(self):
        if self._notification_count == 0 and self._hide_empty:
            self.setVisible(False)
            return

        active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        active_label_content = active_label_content.format(
            count=self._notification_count,
            icon=(self._icons["new"] if self._notification_count > 0 else self._icons["default"]),
        )

        for label in iterate_label_as_parts(self, active_widgets, active_label_content):
            # Update class based on notification count
            if self._notification_count > 0:
                label.setProperty("class", label.property("class") + " new-notification")

        for widget in active_widgets:
            style = widget.style()
            style.unpolish(widget)
            style.polish(widget)
