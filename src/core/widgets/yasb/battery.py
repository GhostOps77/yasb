import re
from datetime import timedelta

import humanize
import psutil
from PyQt6.QtCore import QTimer

from core.utils.utilities import build_widget_label, iterate_label_as_parts
from core.validation.widgets.yasb.battery import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget


class BatteryWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    def __init__(
        self,
        label: str,
        label_alt: str,
        class_name: str,
        update_interval: int,
        time_remaining_natural: bool,
        hide_unsupported: bool,
        callbacks: dict[str, str],
        charging_options: dict[str, str | bool],
        status_thresholds: dict[str, int],
        status_icons: dict[str, str],
        animation: dict[str, str],
        **kwargs,
    ):
        super().__init__(update_interval, class_name=f"battery-widget {class_name}", **kwargs)
        self._time_remaining_natural = time_remaining_natural
        self._status_thresholds = status_thresholds
        self._status_icons = status_icons
        self._battery_state = None
        self._show_alt = False
        self._last_threshold = None
        self._animation = animation
        self._icon_charging_format = charging_options["icon_format"]
        self._icon_charging_blink = charging_options["blink_charging_icon"]
        self._icon_charging_blink_interval = charging_options["blink_interval"]
        self._hide_unsupported = hide_unsupported

        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt

        build_widget_label(self, self._label_content, self._label_alt_content, self._label_shadow)

        self.register_callback("update_label", self._update_label)
        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("timer", self._update_label)
        self.map_callbacks(callbacks)

        self._charging_blink_timer = QTimer(self)
        self._charging_blink_timer.setInterval(self._icon_charging_blink_interval)
        self._charging_blink_timer.timeout.connect(self._charging_blink)
        self._charging_icon_label = None

        self.start_timer()

    def _toggle_label(self):
        self._animate()
        self._show_alt_label = not self._show_alt_label
        # for widget in self._widgets:
        #     widget.setVisible(not self._show_alt_label)
        # for widget in self._widgets_alt:
        #     widget.setVisible(self._show_alt_label)
        self._update_label()

    def _get_time_remaining(self) -> str:
        secs_left = self._battery_state.secsleft
        if secs_left == psutil.POWER_TIME_UNLIMITED:
            time_left = "unlimited"
        elif type(secs_left) == int:
            time_left = timedelta(seconds=secs_left)
            time_left = humanize.naturaldelta(time_left) if self._time_remaining_natural else str(time_left)
        else:
            time_left = "unknown"
        return time_left

    def _get_battery_threshold(self):
        percent = self._battery_state.percent

        if percent <= self._status_thresholds["critical"]:
            return "critical"
        elif self._status_thresholds["critical"] < percent <= self._status_thresholds["low"]:
            return "low"
        elif self._status_thresholds["low"] < percent <= self._status_thresholds["medium"]:
            return "medium"
        elif self._status_thresholds["medium"] < percent <= self._status_thresholds["high"]:
            return "high"
        elif self._status_thresholds["high"] < percent <= self._status_thresholds["full"]:
            return "full"

    def _get_charging_icon(self, threshold: str) -> str:
        icon = self._status_icons[f"icon_{threshold}"]
        if self._battery_state.power_plugged:
            return self._icon_charging_format.format(charging_icon=self._status_icons["icon_charging"], icon=icon)
        return icon

    def _charging_blink(self):
        """Toggle the blink class to create a blinking effect using CSS."""
        label = self._charging_icon_label
        if not label:
            return

        current_classes = label.property("class") or ""

        if "blink" in current_classes:
            new_classes = current_classes.replace("blink", "").strip()
            new_classes = re.sub(r"\s+", " ", new_classes)
        else:
            new_classes = f"{current_classes} blink".strip()

        label.setProperty("class", new_classes)
        label.setStyleSheet("")

    def _update_label(self):
        # active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_widgets = self._widgets
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        self._battery_state = psutil.sensors_battery()

        if self._battery_state is None:
            if self._hide_unsupported:
                self.hide()
                self.timer.stop()
                return

            active_label_content = "Battery info not available"

            for _ in iterate_label_as_parts(self, active_widgets, active_label_content):
                pass

            return

        original_threshold = self._get_battery_threshold()
        threshold = "charging" if self._battery_state.power_plugged else original_threshold
        time_remaining = self._get_time_remaining()
        is_charging_str = "yes" if self._battery_state.power_plugged else "no"
        charging_icon = self._get_charging_icon(original_threshold)

        active_label_content = active_label_content.format(
            percent=self._battery_state.percent,
            time_remaining=time_remaining,
            is_charging=is_charging_str,
            icon=charging_icon,
        )

        threshold_class_name = f"status-{threshold}"

        for label in iterate_label_as_parts(
            self, active_widgets, active_label_content, "alt" if self._show_alt_label else ""
        ):
            # apply status‐class
            class_names = label.property("class") + f" {threshold_class_name}"

            # only blink when plugged AND blink_enabled
            if self._battery_state.power_plugged and self._icon_charging_blink:
                self._charging_icon_label = label
                if not self._charging_blink_timer.isActive():
                    self._charging_blink_timer.start()
            else:
                if self._charging_blink_timer.isActive():
                    self._charging_blink_timer.stop()
                self._charging_icon_label = None

                if "blink" in class_names:
                    class_names.replace("blink", "")

            label.setProperty("class", class_names)
            label.setStyleSheet("")
