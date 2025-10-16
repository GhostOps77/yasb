import json
import subprocess
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from core.utils.utilities import build_widget_label, iterate_label_as_parts
from core.utils.win32.system_function import function_map
from core.validation.widgets.yasb.custom import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget, TruncatedLabel


class CustomWorker(QObject):
    finished = pyqtSignal()
    data_ready = pyqtSignal(object)

    def __init__(self, cmd, use_shell, encoding, return_type, hide_empty):
        super().__init__()
        self.cmd = cmd
        self.use_shell = use_shell
        self.encoding = encoding
        self.return_type = return_type
        self.hide_empty = hide_empty

    def run(self):
        exec_data = None
        if self.cmd:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=self.use_shell,
                encoding=self.encoding,
            )
            output = proc.stdout.read()
            if self.return_type == "json":
                try:
                    exec_data = json.loads(output)
                except json.JSONDecodeError:
                    exec_data = None
            else:
                exec_data = output.decode("utf-8").strip()
        self.data_ready.emit(exec_data)
        self.finished.emit()


class CustomWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA
    label_cls = TruncatedLabel

    def __init__(
        self,
        label: str,
        label_alt: str,
        label_placeholder: str,
        label_max_length: int,
        exec_options: dict,
        animation: dict[str, str],
        class_name: str,
        callbacks: dict[str, str],
        **kwargs,
    ):
        super().__init__(exec_options["run_interval"], class_name=f"custom-widget {class_name}", **kwargs)
        self._label_max_length = label_max_length
        self._exec_data = None
        self._exec_cmd = exec_options["run_cmd"].split(" ") if exec_options.get("run_cmd", False) else None
        self._exec_return_type = exec_options["return_format"]
        self._exec_shell = exec_options["use_shell"]
        self._exec_encoding = exec_options["encoding"]
        self._hide_empty = exec_options["hide_empty"]
        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt
        self._label_placeholder = label_placeholder
        self._animation = animation

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("exec_custom", self._exec_callback)
        self.register_callback("timer", self._exec_callback)
        self.map_callbacks(callbacks)

        build_widget_label(self, self._label_content, self._label_alt_content)

        if exec_options["run_once"]:
            self._exec_callback()
        else:
            self.start_timer()

    def _toggle_label(self):
        self._animate()
        self._show_alt_label = not self._show_alt_label
        # for widget in self._widgets:
        #     widget.setVisible(not self._show_alt_label)
        # for widget in self._widgets_alt:
        #     widget.setVisible(self._show_alt_label)
        self._update_label()

    # def _create_dynamically_label(self, content: str, content_alt: str = ""):
    #     give_pointing_cursor = any(
    #         cb != "do_nothing"
    #         for cb in [self.callbacks["on_left"], self.callbacks["on_right"], self.callbacks["on_middle"]]
    #     )

    #     def process_content(content, is_alt=False):
    #         widgets = []

    #         for label in iterate_label_as_parts(
    #             self,
    #             widgets,
    #             content,
    #             "label alt" if is_alt else "label",
    #             self._widget_container_layout,
    #             self._label_shadow,
    #         ):
    #             if give_pointing_cursor:
    #                 label.setCursor(Qt.CursorShape.PointingHandCursor)
    #             # label.setVisible(is_alt)

    #         return widgets

    #     self._widgets = process_content(content)
    #     # self._widgets_alt = process_content(content_alt, is_alt=True)

    def _update_label(self):
        active_widgets = self._widgets
        # active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        active_label_content = active_label_content.format(data=self._exec_data)

        for _ in iterate_label_as_parts(active_widgets, active_label_content, layout=self._widget_container_layout):
            ...

        self.setVisible(bool(self._exec_data) or not self._hide_empty)

    def _exec_callback(self):
        if self._exec_cmd:
            worker = CustomWorker(
                self._exec_cmd,
                self._exec_shell,
                self._exec_encoding,
                self._exec_return_type,
                self._hide_empty,
            )
            worker_thread = threading.Thread(target=worker.run)
            worker.data_ready.connect(self._handle_exec_data)
            worker.finished.connect(worker.deleteLater)
            worker_thread.start()
        else:
            self._update_label()

    def _handle_exec_data(self, exec_data):
        self._exec_data = exec_data
        self._update_label()

    def _cb_execute_subprocess(self, cmd: str, *cmd_args: list[str]):
        # Overrides the default 'exec' callback from BaseWidget to allow for data formatting
        if self._exec_data:
            for idx, cmd_arg in range(len(cmd_args)):
                try:
                    cmd_args[idx].append(cmd_arg.format(data=self._exec_data))
                except KeyError:
                    cmd_args[idx].append(cmd_args)

        if cmd in function_map:
            function_map[cmd]()
        else:
            subprocess.Popen([cmd, *cmd_args], shell=self._exec_shell, encoding=self._exec_encoding)
