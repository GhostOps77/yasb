import logging
import os
import re
from dataclasses import dataclass
from typing import Literal, TypedDict

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from watchdog.events import DirCreatedEvent, FileCreatedEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from core.validation.widgets.yasb.file_watcher import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget

logger = logging.getLogger("filewatcher_widget")


class ListenPaths(TypedDict):
    directory: str
    patterns: list[str] | None
    ignore_patterns: list[str]
    ignore_directories: bool
    read_file_contents: bool
    read_max_bytes: int


@dataclass(slots=True)
class FileEntity:
    path: str
    type: Literal["file", "folder"]
    content: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @classmethod
    def from_path(
        cls, path: str, read_file_contents: bool = False, read_max_bytes: int = 65536
    ):
        is_file = os.path.isfile(path)
        content = ""

        if read_file_contents and is_file:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(read_max_bytes)
            except Exception:
                content = ""

        return cls(
            path=path,
            type="file" if is_file else "folder",
            content=content,
        )


@dataclass(slots=True)
class FileEventObject:
    action: str
    src: FileEntity
    dest: FileEntity | None = None


class FileEventEmitter(QObject):
    event_occurred = pyqtSignal(object)  # will emit EventPayload


class WatchDogHandler(PatternMatchingEventHandler):
    def __init__(
        self,
        emitter: FileEventEmitter,
        patterns: list[str],
        ignore_patterns: list[str],
        ignore_directories: bool,
        read_file_contents: bool,
        read_max_bytes: int,
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=True
        )
        self.emitter = emitter
        self.read_file_contents = read_file_contents
        self.read_max_bytes = read_max_bytes

    def on_created(self, event):
        logger.debug(f'Created {event.src_path}')
        print(f'Created {event.src_path}')
        self._emit("created", event)

    def on_modified(self, event):
        logger.debug(f'Modified {event.src_path}')
        self._emit("modified", event)

    def on_deleted(self, event):
        logger.debug(f'Deleted {event.src_path}')
        self._emit("deleted", event)

    def on_moved(self, event):
        dest_path = getattr(event, "dest_path", event.src_path)
        logger.debug(f'Moved {event.src_path} -> {dest_path}')
        self._emit("moved", event)

    def _emit(self, action: str, event: DirCreatedEvent | FileCreatedEvent):
        src_path = event.src_path
        dest_path = getattr(event, "dest_path", None)

        src_entity = FileEntity.from_path(
            src_path, self.read_file_contents, self.read_max_bytes
        )
        dest_entity = FileEntity.from_path(dest_path) if dest_path is not None else None
        event_obj = FileEventObject(action, src_entity, dest_entity)
        self.emitter.event_occurred.emit(event_obj)


class FileWatcherWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    def __init__(
        self,
        listen_paths: list[ListenPaths],
        label_max_length: int,
        clear_labels_after_interval: int,
        labels: dict[str, dict[str, str]],
        container_padding: dict[str, int] | None = None,
    ):
        # if common_patterns:
        #     config_path = get_config_path()
        #     raise_info_alert(
        #         title="Failed to load recently updated config file.",
        #         msg=f"The file '{config_path}' contains validation error(s) and has not been loaded.",
        #         informative_msg="For more information, click 'Show Details'.",
        #         additional_details=
        #             "The yasb.file_watcher.FileWatcher widget received common pattern values " \
        #             "in the 'patterns' and 'ignore_patterns' options." \
        #             '\n -'.join(common_patterns)
        #     )
        #     return

        super().__init__(class_name="file-watcher")

        self.listen_paths = listen_paths
        self._padding = container_padding
        self._event_based_labels = labels

        self._label_content = ""
        self.label_max_length = label_max_length

        self._widget_container_layout = QHBoxLayout()
        self._widget_container_layout.setContentsMargins(0, 0, 0, 0)
        self._widget_container_layout.setSpacing(0)
        self._widget_container_layout.setContentsMargins(
            self._padding["left"],
            self._padding["top"],
            self._padding["right"],
            self._padding["bottom"],
        )

        self._widget_container = QFrame()
        self._widget_container.setLayout(self._widget_container_layout)
        self.widget_layout.addWidget(self._widget_container)

        self._update_label(self._label_content)

        # signals and watchdog
        self._emitter = FileEventEmitter()
        self._emitter.event_occurred.connect(self._on_event_main_thread)

        self._observer = Observer()

        # small debounce timer to avoid rapid UI thrashing; collects last label
        self._debounce_timer = QTimer()
        self._debounce_timer.setInterval(50)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_label_to_ui)
        self._pending_label_content = None

        self._clear_labels_after_interval = clear_labels_after_interval
        if self._clear_labels_after_interval is not None and self._clear_labels_after_interval > 0:
            self._fadeout_timer = QTimer()
            self._fadeout_timer.setInterval(self._clear_labels_after_interval)
            self._fadeout_timer.setSingleShot(True)
            self._fadeout_timer.timeout.connect(self._clear_labels)

        self._start_observer()

    def _start_observer(self):
        def remove_duplicate_paths(paths: list[str]):
            return list({
                os.path.expanduser(os.path.expandvars(s.strip()))
                for s in paths
            })

        for path in self.listen_paths:
            path['directory'] = os.path.expanduser(
                os.path.expandvars(path['directory'].strip())
            )

            handler = WatchDogHandler(
                self._emitter,
                remove_duplicate_paths(path['patterns']),
                remove_duplicate_paths(path['ignore_patterns']),
                path['ignore_directories'],
                path['read_file_contents'],
                path['read_max_bytes'],
            )

            self._observer.schedule(
                handler, path['directory'], recursive=not path['ignore_directories']
            )

        self._observer.start()
        logger.info('FileWatcher: Observer started and running')

    def _stop_observer(self):
        """Stop observer and cleanup (called by YASB shutdown)"""
        logger.info('FileWidget: Stopping File watcher...')
        try:
            if self._observer.is_alive():
                self._observer.stop()
                self._observer.join(timeout=2)
                logger.info("FileWidget: Stopped observer")
        except Exception:
            pass

    def _on_event_main_thread(self, payload: FileEventObject):
        label_content = self._event_based_labels[payload.src.type].get(payload.action, "")
        if not label_content:
            self.setVisible(False)
            return

        if self.isHidden():
            self.setVisible(True)

        self._queue_label_update(label_content.format(data=payload))
        if self._clear_labels_after_interval is not None:
            self._fadeout_timer.start()  # reset timer on every event

    def _clear_labels(self):
        for lbl in self._widgets:
            lbl.clear()         # clears text
            lbl.hide()          # or fade out if you want

    def _update_label(self, content: str):
        label_parts = re.split(r"(<span[^>]*?>.*?</span>)", content)
        active_widget = self._widgets
        active_widget_len = len(active_widget)
        widgets_index = 0

        for part in label_parts:
            part = part.strip()
            if not part:
                continue

            class_result = 'icon'
            if part.startswith("<span") and part.endswith("</span>"):
                class_name = re.search(r'class=(["\'])([^"\']+?)\1', part)
                if class_name:
                    class_result = class_name.group(2)
                part = re.sub(r"<span[^>]*?>|</span>", "", part).strip()

            if widgets_index < active_widget_len:
                label = active_widget[widgets_index]
                label.setText(part)
                label.setProperty("class", class_result)
                # label.style().unpolish(label)
                # label.style().polish(label)
                if label.isHidden():
                    label.setVisible(True)
                widgets_index += 1
            else:
                label = QLabel(part)
                label.setProperty("class", class_result)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._widget_container_layout.addWidget(label)
                active_widget.append(label)

        for i in range(widgets_index, active_widget_len):
            active_widget[i].setVisible(False)


    def _queue_label_update(self, text: str):
        """
        Debounce rapid events: schedule a small timer; keep last label.
        """
        logger.debug(f'FileWidget: Updating pending label content to {text}')
        self._pending_label_content = text
        if not self._debounce_timer.isActive():
            self._debounce_timer.start()

    def _emit_label_to_ui(self):
        """
        Called on main thread by debounce timer. Use build_widget_label to update widgets.
        """
        if self._pending_label_content is None:
            return

        self._label_content = self._pending_label_content

        try:
            # clear layout widgets
            layout = self._widget_container_layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()  # Schedule widget for deletion
        except Exception:
            pass

        # recreate labels
        self._update_label(self._label_content)

        # If BaseWidget.update exists and expected, call it so YASB knows widget changed.
        try:
            for widget in self._widgets:
                self._widget_container_layout.addWidget(widget)
        except Exception:
            # fallback: do nothing
            pass

    def _truncate_label(self, label):
        if self._label_max_length and len(label) > self._label_max_length:
            return label[: self._label_max_length] + "..."
        return label

    def closeEvent(self, event):
        self._stop_observer()
        super().closeEvent(event)
