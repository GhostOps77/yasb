import datetime
import hashlib
import json
import os
import urllib.request
import webbrowser
from typing import Callable

from PyQt6.QtCore import QThread, QTimer, pyqtSignal

from core.utils.tooltip import set_tooltip
from core.utils.utilities import ToastNotifier, build_widget_label, iterate_label_as_parts
from core.validation.widgets.yasb.glucose_monitor import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget
from settings import SCRIPT_PATH


class GlucoseMonitorWorker(QThread):
    @classmethod
    def get_instance(cls):
        return cls()

    status_updated = pyqtSignal(int, float, str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._url: str | None = None
        self.running = True

    def set_url(self, host: str, secret: str) -> None:
        secret_hash = hashlib.sha1(secret.encode()).hexdigest()
        self._url = f"{host}/api/v1/entries/current.json?secret={secret_hash}"

    def stop(self) -> None:
        self.running = False
        self.wait()

    def run(self) -> None:
        if not self.running:
            return

        try:
            with urllib.request.urlopen(self._url) as response:
                data = json.loads(response.read().decode("utf-8"))
                status = response.status

            if status != 200:
                raise RuntimeError(f"Response status code should be 200 but got {status}")

            resp_json = data[0]
            self.status_updated.emit(
                resp_json["sgv"],
                resp_json["delta"],
                resp_json["dateString"],
                resp_json["direction"],
            )
        except Exception:
            self.error_signal.emit("Connection error")


class GlucoseMonitor(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    update_interval_in_milliseconds = 1 * 60 * 1_000
    datetime_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    direction_icons_mapping = {
        "double_up": "DoubleUp",
        "single_up": "SingleUp",
        "forty_five_up": "FortyFiveUp",
        "flat": "Flat",
        "forty_five_down": "FortyFiveDown",
        "single_down": "SingleDown",
        "double_down": "DoubleDown",
    }

    def __init__(
        self,
        label: str,
        error_label: str,
        tooltip: str,
        host: str,
        secret: str,
        secret_env_name: str,
        direction_icons: dict[str, str],
        sgv_measurement_units: str,
        sgv_range: dict,
        callbacks: dict[str, str],
        notify_on_error: bool,
        label_shadow: dict | None = None,
        container_shadow: dict | None = None,
    ) -> None:
        super().__init__(
            timer_interval=self.update_interval_in_milliseconds,
            class_name="cgm-widget",
            callbacks=callbacks,
            label_shadow=label_shadow,
            container_shadow=container_shadow,
        )

        self._error_message: str | None = None
        self._notify_on_error: bool = notify_on_error
        self._is_sgv_in_range: bool = False

        self._label_content = label
        self._error_label_content = error_label
        self._tooltip = tooltip
        self._host = host
        self._secret = secret != "env" and secret or os.getenv(secret_env_name)
        self._label_shadow = label_shadow
        self._container_shadow = container_shadow

        self._direction_icons = {self.direction_icons_mapping[key]: value for key, value in direction_icons.items()}

        self._sgv_measurement_units = sgv_measurement_units
        self._available_sgv_measurement_units: dict[str, Callable[[int | float], str]] = {
            "mg/dl": lambda sgv: str(round(sgv)),
            "mmol/l": lambda sgv: f"{sgv / 18:.1f}",
        }

        if not (convert_sgv := self._available_sgv_measurement_units.get(self._sgv_measurement_units)):
            raise ValueError("Wrong measurement units")
        self._convert_sgv = convert_sgv

        self._sgv_range = {key: float(value) for key, value in sgv_range.items()}

        self._icon_path = os.path.join(SCRIPT_PATH, "assets", "images", "app_transparent.png")
        self._status_data = {}

        build_widget_label(self, self._label_content, self._error_label_content)

        self.register_callback("open_cgm", self._open_cgm)

        self._worker = GlucoseMonitorWorker.get_instance()
        self._worker.set_url(self._host, self._secret)
        self._worker.status_updated.connect(self._handle_status_update)
        self._worker.error_signal.connect(self._handle_error_signal)

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._worker.start)
        self._update_timer.start(self.update_interval_in_milliseconds)

        self._worker.start()

    def _open_cgm(self) -> None:
        webbrowser.open(self._host)

    def _update_label(self) -> None:
        error_msg_exists = bool(self._error_message)

        for widget in self._widgets:
            widget.setVisible(not error_msg_exists)

        for widget in self._widgets_alt:
            widget.setVisible(error_msg_exists)

        if self._error_message:
            format_data = {"error_message": self._error_message}
        else:
            format_data = self._status_data

        active_widgets = self._error_message and self._widgets_alt or self._widgets
        active_label_content = self._error_message and self._error_label_content or self._label_content
        active_label_content = active_label_content.format_map(format_data)

        for label in iterate_label_as_parts(self, active_widgets, active_label_content):
            if label.is_icon:
                current_class = label.property("class")
                if "sgv" in current_class.split():
                    new_class = self._is_sgv_in_range and "sgv in-range" or "sgv out-range"
                    label.setProperty("class", f"label icon {new_class}")
                    label._reload_css()

        if self._tooltip:
            set_tooltip(
                widget=self._widget_container,
                text=self._error_message or self._tooltip.format_map(self._status_data),
            )

    def _handle_error_signal(self, message: str) -> None:
        prev_error_message = self._error_message
        self._error_message = message
        self._update_label()

        if self._notify_on_error and not prev_error_message:
            toaster = ToastNotifier()
            toaster.show(self._icon_path, "Glucose Monitor", message)

    def _handle_status_update(
        self,
        sgv: int,
        sgv_delta: float,
        date_string: str,
        direction: str,
    ) -> None:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        last_update_time = datetime.datetime.strptime(date_string, self.datetime_format)
        delta_time_in_minutes = (now - last_update_time).total_seconds() // 60
        direction = self._direction_icons[direction]

        sgv = self._convert_sgv(sgv)
        sgv_delta = self._convert_sgv(sgv_delta)

        self._status_data = {
            "sgv": sgv,
            "sgv_delta": sgv_delta,
            "delta_time_in_minutes": delta_time_in_minutes,
            "direction": direction,
        }

        sgv_as_float = float(sgv)
        self._is_sgv_in_range = self._sgv_range["min"] <= sgv_as_float <= self._sgv_range["max"]

        self._error_message = None
        self._update_label()
