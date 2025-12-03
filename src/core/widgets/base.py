import logging
import shlex
import subprocess
from typing import Callable, Sequence, TypedDict, cast

from PyQt6.QtCore import Qt, QThread, QTimer
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QBoxLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QStyle, QVBoxLayout, QWidget

from core.ui.style import build_button_styles, build_link_button_style
from core.utils.widgets.animation_manager import AnimationManager
from core.utils.win32.system_function import function_map


class PaddingsDict(TypedDict):
    left: int
    right: int
    top: int
    bottom: int


type Padding = PaddingsDict | Sequence[int] | int | float


class BaseFrameMixin:
    def __init__(self, *args, class_name: str = "", shadows: dict = None, **kwargs):
        super().__init__(*args, **kwargs)
        if shadows is not None:
            self.add_shadows(shadows)
        self.setProperty("class", class_name)
        self.setContentsMargins(0, 0, 0, 0)

    def add_shadows(self, shadows: dict) -> None:
        from core.utils.utilities import add_shadow

        add_shadow(self, shadows)


class BaseFrame(BaseFrameMixin, QFrame):
    def __init__(self, *args, class_name: str = "", shadows: dict = None, **kwargs):
        super().__init__(*args, class_name=class_name, shadows=shadows, **kwargs)


class BasePushButton(BaseFrameMixin, QPushButton):
    def __init__(
        self,
        *args,
        on_click: Callable[[], None] | None = None,
        style_variant: str | None = None,
        class_name: str = "",
        shadows: dict = None,
        **kwargs,
    ):
        super().__init__(*args, class_name=class_name, shadows=shadows, **kwargs)

        if on_click is not None:
            self.clicked.connect(on_click)
        if style_variant is not None:
            self.apply_style(style_variant)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def apply_style(self, variant: str = "primary") -> str:
        styles = build_button_styles()
        try:
            style_sheet = styles[variant]
        except KeyError as exc:
            raise ValueError(f"Unknown button style variant: {variant}") from exc
        self.setStyleSheet(style_sheet)
        return style_sheet

    def apply_link_button_style(self) -> str:
        style_sheet = build_link_button_style()
        self.setStyleSheet(style_sheet)
        return style_sheet


class BaseLabel(BaseFrameMixin, QLabel):
    def __init__(self, *args, class_name: str = "", shadows: dict = None, **kwargs):
        super().__init__(*args, class_name=class_name, shadows=shadows, **kwargs)

        self.is_icon: bool = False
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setTextFormat(Qt.TextFormat.PlainText)

    def add_class(self, class_name: str):
        old_class_name = self.property("class").strip()
        self.setProperty("class", f"{old_class_name} {class_name}")

    def _reload_css(self):
        style = self.style()
        if not style:
            return

        try:
            style = cast(QStyle, self.style())
            style.unpolish(self)
            style.polish(self)
        except Exception:
            pass

        self.update()


class BaseYasbWidgetLabel(BaseLabel):
    def __init__(self, text, *args, class_name: str = "", shadows: dict | None = None, **kwargs):
        super().__init__(text, *args, class_name=class_name, shadows=shadows, **kwargs)
        self.setProperty("class", "label " + self.property("class"))


class TruncatedLabel(BaseYasbWidgetLabel):
    def __init__(self, *args, label_max_len: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_max_len = label_max_len
        if label_max_len is not None:
            self.setText(self._truncate_label(self.text()))

    def setText(self, text: str):
        if self.label_max_len is not None:
            text = self._truncate_label(text)
        super().setText(text)

    def _truncate_label(self, text: str):
        if self.label_max_len and len(text) > self.label_max_len:
            text = text[: self.label_max_len - 3] + "..."
        return text


class BaseBoxLayout(BaseFrameMixin, QBoxLayout):
    def __init__(self, *args, spacing: int = 0, paddings: Padding | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        if paddings is None:
            paddings = {}

        elif isinstance(paddings, Sequence):
            assert len(paddings) == 4, "Length of padding list is not equal to 4."
            paddings = dict(zip(("top", "right", "bottom", "left"), paddings))

        elif isinstance(paddings, (int, float)):
            paddings = dict.fromkeys(("top", "right", "bottom", "left"), paddings)

        paddings = cast(PaddingsDict, paddings)

        self.setContentsMargins(
            paddings.get("left", 0), paddings.get("top", 0), paddings.get("right", 0), paddings.get("bottom", 0)
        )
        self.setSpacing(spacing)

    def addWidgets(self, *widgets: QWidget):
        for widget in widgets:
            self.addWidget(widget)


class BaseHBoxLayout(BaseBoxLayout, QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(QBoxLayout.Direction.LeftToRight, *args, **kwargs)


class BaseVBoxLayout(BaseBoxLayout, QVBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(QBoxLayout.Direction.TopToBottom, *args, **kwargs)


class BaseWidget(QWidget):
    validation_schema: dict = None
    event_listener: QThread = None
    label_cls: type[BaseYasbWidgetLabel] = BaseYasbWidgetLabel

    def __init__(
        self,
        timer_interval: int = None,
        class_name: str = "",
        callbacks: dict[str, str] = None,
        label_shadow: dict | None = None,
        container_padding: dict[str, int] = None,
        container_shadow: dict | None = None,
    ):
        super().__init__()
        self.timer_interval = timer_interval
        self.bar = None
        self.bar_id = None
        self.monitor_hwnd = None
        self._label_shadow = label_shadow

        if callbacks is not None:
            self._callbacks = {
                "on_left": "on_left",
                "on_middle": "on_middle",
                "on_right": "on_right",
                "timer": "timer",
                "default": "default",
                "do_nothing": "do_nothing",
                "exec": "exec",
            } | callbacks

        self.timer = QTimer(self)
        self.mousePressEvent = self._handle_mouse_events

        #    ___________________________________________________________________________
        #   |
        #   |   Base Widget
        #   |   Layout = widget layout
        #   |   Default class name = ""
        #   |
        #   |    _______________________________________________________________________
        #   |   |
        #   |   |   Widget Frame
        #   |   |   Layout = widget frame layout
        #   |   |   Default class name = "widget"
        #   |   |
        #   |   |    ___________________________________________________________________
        #   |   |   |
        #   |   |   |   Widget Container
        #   |   |   |   Layout = widget container layout
        #   |   |   |   Default class name = "widget-container"
        #   |   |   |
        #   |   |   |    _______________________________________     ___________________
        #   |   |   |   |                                       |   |
        #   |   |   |   |    Base Label                         |   |   More labels ...
        #   |   |   |   |    Default class name = "label"       |   |
        #   |   |   |   |_______________________________________|   |___________________
        #   |   |   |

        # Initialize container and its layout (Inner Layer).
        self._widget_container_layout = BaseHBoxLayout(paddings=container_padding)
        self._widget_container = BaseFrame(class_name="widget-container", shadows=container_shadow)
        self._widget_container.setLayout(self._widget_container_layout)

        # Initialize main widget frame and its layout (Middle Layer).
        self._widget_frame = BaseFrame(class_name=f"widget {class_name}")
        self._widget_frame_layout = BaseHBoxLayout()
        self._widget_frame.setLayout(self._widget_frame_layout)

        # Add the container to the main frame layout
        self._widget_frame_layout.addWidget(self._widget_container)

        # Add a layout to the current widget (Outer Layer).
        self.widget_layout = BaseHBoxLayout()
        self.setLayout(self.widget_layout)

        # Add the widget frame to the current widget.
        self.widget_layout.addWidget(self._widget_frame)

        self._registered_callbacks = {
            "on_left": self._cb_do_nothing,
            "on_middle": self._cb_do_nothing,
            "on_right": self._cb_do_nothing,
            "timer": self._cb_do_nothing,
            "default": self._cb_do_nothing,
            "do_nothing": self._cb_do_nothing,
            "exec": self._cb_execute_subprocess,
        }

    def init_label(self, text: str, *args, class_name: str = "", **kwargs):
        shadows = getattr(self, "_label_shadow", None)
        return self.label_cls(text, *args, class_name=class_name, shadows=shadows, **kwargs)

    def register_callback(self, callback_name: str, fn: Callable[[], None]):
        self._registered_callbacks[callback_name] = fn

    def start_timer(self):
        if self.timer_interval and self.timer_interval > 0:
            self.timer.timeout.connect(self._timer_callback)
            self.timer.start(self.timer_interval)
        self._timer_callback()

    def _handle_mouse_events(self, event: QMouseEvent):
        event_btn = event.button()
        if event_btn == Qt.MouseButton.LeftButton:
            self._run_callback(self._callbacks["on_left"])

        elif event_btn == Qt.MouseButton.MiddleButton:
            self._run_callback(self._callbacks["on_middle"])

        elif event_btn == Qt.MouseButton.RightButton:
            self._run_callback(self._callbacks["on_right"])

    def _animate(self):
        if hasattr(self, "_animation") and self._animation["enabled"]:
            AnimationManager.animate(self, self._animation["type"], self._animation["duration"])

    def _run_callback(self, callback_str: str):
        callback_type, *callback_args = shlex.split(callback_str)
        is_valid_callback = callback_type in self._registered_callbacks
        callback = self._registered_callbacks[callback_type if is_valid_callback else "default"]

        try:
            callback(*callback_args)
        except Exception:
            logging.exception(f"Failed to execute callback of type '{callback_type}' with args: {callback_args}")

    def _timer_callback(self):
        self._run_callback(self._callbacks["timer"])

    def _cb_execute_subprocess(self, cmd: str, *cmd_args: list[str]):
        if cmd in function_map:
            function_map[cmd]()
        else:
            subprocess.Popen([cmd, *cmd_args] if cmd_args else [cmd], shell=True)

    def _cb_do_nothing(self):
        pass
