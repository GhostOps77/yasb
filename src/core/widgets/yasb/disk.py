import os

import psutil
import win32api
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from core.utils.utilities import (
    PopupWidget,
    build_progress_widget,
    build_widget_label,
    iterate_label_as_parts,
)
from core.validation.widgets.yasb.disk import VALIDATION_SCHEMA
from core.widgets.base import BaseVBoxLayout, BaseWidget


class ClickableDiskWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DiskWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    def __init__(
        self,
        label: str,
        label_alt: str,
        class_name: str,
        volume_label: str,
        decimal_display: int,
        update_interval: int,
        group_label: dict[str, str],
        animation: dict[str, str],
        disk_thresholds: dict[str, int],
        label_shadow: dict = None,
        progress_bar: dict = None,
        **kwargs,
    ):
        super().__init__(int(update_interval * 1000), class_name=f"disk-widget {class_name}", **kwargs)

        self._decimal_display = decimal_display
        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt
        self._volume_label = volume_label.upper()
        self._group_label = group_label
        self._animation = animation
        self._label_shadow = label_shadow
        self._disk_thresholds = disk_thresholds
        self._progress_bar = progress_bar

        self.progress_widget = build_progress_widget(self, self._progress_bar)

        build_widget_label(self, self._label_content, self._label_alt_content)

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("toggle_group", self._toggle_group)
        self.register_callback("update_label", self._update_label)
        self.register_callback("timer", self._update_label)

        self.start_timer()

    def _toggle_label(self):
        self._animate()
        self._show_alt_label = not self._show_alt_label
        # for widget in self._widgets:
        #     widget.setVisible(not self._show_alt_label)
        # for widget in self._widgets_alt:
        #     widget.setVisible(self._show_alt_label)
        self._update_label()

    def _toggle_group(self):
        self._animate()
        self.show_group_label()

    def _update_label(self):
        # active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_widgets = self._widgets
        # active_widgets_len = len(active_widgets)
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content

        try:
            disk_space = self._get_space()
        except Exception:
            disk_space = None

        percent_value = 0
        if disk_space:
            percent_str = disk_space["used"]["percent"]
            # if isinstance(percent_str, str) and percent_str.endswith("%"):
            percent_value = float(percent_str.strip("%"))
            # else:
            #     percent_value = float(percent_str)
            active_label_content = active_label_content.format(space=disk_space, volume_label=self._volume_label)

        add_progress_widget = False
        if self._progress_bar["enabled"] and self.progress_widget:
            if self._widget_container_layout.indexOf(self.progress_widget) != -1:
                self._widget_container_layout.removeWidget(self.progress_widget)
                add_progress_widget = True
            self.progress_widget.set_value(percent_value)

        disk_status_class = f"status-{self._get_disk_threshold(percent_value)}"

        for label in iterate_label_as_parts(
            self, active_widgets, active_label_content, "alt" if self._show_alt_label else ""
        ):
            # Update label with formatted content
            label.setProperty("class", label.property("class") + " " + disk_status_class)
            label.setStyleSheet("")

        if add_progress_widget:
            if self._progress_bar["position"] == "left":
                insert_position = 0
            else:
                insert_position = self._widget_container_layout.count()

            self._widget_container_layout.insertWidget(self.progress_widget, insert_position)

    def _get_volume_label(self, drive_letter):
        if not self._group_label["show_label_name"]:
            return

        try:
            return win32api.GetVolumeInformation(f"{drive_letter}:\\")[0]
        except Exception:
            return

    def show_group_label(self):
        self.dialog = PopupWidget(
            self,
            self._group_label["blur"],
            self._group_label["round_corners"],
            self._group_label["round_corners_type"],
            self._group_label["border_color"],
        )
        self.dialog.setProperty("class", "disk-group")

        layout = QVBoxLayout()
        for label in self._group_label["volume_labels"]:
            disk_space = self._get_space(label)
            if disk_space is None:
                continue

            row_widget = QWidget()
            row_widget.setProperty("class", "disk-group-row")

            volume_label = self._get_volume_label(label)
            display_label = f"{volume_label} ({label}):" if volume_label else f"{label}:"

            clicable_row = ClickableDiskWidget(label)
            clicable_row.clicked.connect(lambda lbl=label: self.open_explorer(lbl))
            clicable_row.setCursor(Qt.CursorShape.PointingHandCursor)

            v_layout = QVBoxLayout(clicable_row)
            h_layout = QHBoxLayout()

            label_widget = QLabel(display_label)
            label_widget.setProperty("class", "disk-group-label")
            h_layout.addWidget(label_widget)

            label_size = QLabel()
            label_size.setProperty("class", "disk-group-label-size")

            # show size in TB if it's more than 1000GB
            total_gb = float(disk_space["total"]["gb"].strip("GB"))
            if total_gb > 1000:
                total_size = disk_space["total"]["tb"]
            else:
                total_size = disk_space["total"]["gb"]

            free_gb = float(disk_space["free"]["gb"].strip("GB"))
            if free_gb > 1000:
                free_size = disk_space["free"]["tb"]
            else:
                free_size = disk_space["free"]["gb"]

            label_size.setText(f"{free_size} / {total_size}")
            h_layout.addStretch()
            h_layout.addWidget(label_size)

            v_layout.addLayout(h_layout)

            progress_bar = QProgressBar()
            progress_bar.setTextVisible(False)
            progress_bar.setProperty("class", "disk-group-label-bar")
            if disk_space:
                # progress_bar.setValue(int(float(disk_space["used"]["percent"].strip("%"))))
                progress_bar.setValue(int(disk_space["used"]["percent"].strip("%")))
            v_layout.addWidget(progress_bar)

            row_widget_layout = BaseVBoxLayout(row_widget)
            row_widget_layout.addWidget(clicable_row)

            layout.addWidget(row_widget)

        self.dialog.setLayout(layout)

        # Position the dialog
        self.dialog.adjustSize()
        self.dialog.setPosition(
            alignment=self._group_label["alignment"],
            direction=self._group_label["direction"],
            offset_left=self._group_label["offset_left"],
            offset_top=self._group_label["offset_top"],
        )
        self.dialog.show()

    def open_explorer(self, label):
        os.startfile(f"{label}:\\")

    def _get_space(self, volume_label=None):
        if volume_label is None:
            volume_label = self._volume_label

        partitions = psutil.disk_partitions()
        specific_partitions = (partition for partition in partitions if partition.device in f"{volume_label}:\\")
        # if not specific_partitions:
        #     return

        for partition in specific_partitions:
            usage = psutil.disk_usage(partition.mountpoint)
            percent_used = usage.percent
            percent_free = 100 - percent_used
            return {
                "total": {
                    "mb": f"{usage.total / (1024**2):.{self._decimal_display}f}MB",
                    "gb": f"{usage.total / (1024**3):.{self._decimal_display}f}GB",
                    "tb": f"{usage.total / (1024**4):.{self._decimal_display}f}TB",
                },
                "free": {
                    "mb": f"{usage.free / (1024**2):.{self._decimal_display}f}MB",
                    "gb": f"{usage.free / (1024**3):.{self._decimal_display}f}GB",
                    "tb": f"{usage.free / (1024**4):.{self._decimal_display}f}TB",
                    "percent": f"{percent_free:.{self._decimal_display}f}%",
                },
                "used": {
                    "mb": f"{usage.used / (1024**2):.{self._decimal_display}f}MB",
                    "gb": f"{usage.used / (1024**3):.{self._decimal_display}f}GB",
                    "tb": f"{usage.used / (1024**4):.{self._decimal_display}f}TB",
                    "percent": f"{percent_used:.{self._decimal_display}f}%",
                },
            }

        return

    def _get_disk_threshold(self, disk_percent) -> str:
        if disk_percent <= self._disk_thresholds["low"]:
            return "low"
        elif self._disk_thresholds["low"] < disk_percent <= self._disk_thresholds["medium"]:
            return "medium"
        elif self._disk_thresholds["medium"] < disk_percent <= self._disk_thresholds["high"]:
            return "high"
        elif self._disk_thresholds["high"] < disk_percent:
            return "critical"
