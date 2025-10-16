import ctypes
import logging
from ctypes import wintypes

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QPushButton

from core.utils.utilities import PopupWidget, build_widget_label, iterate_label_as_parts
from core.utils.win32.bindings import (
    PowerEnumerate,
    PowerGetActiveScheme,
    PowerReadFriendlyName,
    PowerSetActiveScheme,
)
from core.utils.win32.structs import GUID
from core.validation.widgets.yasb.power_plan import VALIDATION_SCHEMA
from core.widgets.base import BaseFrame, BaseVBoxLayout, BaseWidget


class PowerPlanWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    _instances: list["PowerPlanWidget"] = []
    _shared_timer: QTimer | None = None

    def __init__(
        self,
        label: str,
        label_alt: str,
        class_name: str,
        update_interval: int,
        menu: dict,
        callbacks: dict[str, str],
        **kwargs,
    ):
        super().__init__(class_name=f"power-plan-widget {class_name}", **kwargs)

        self._label = label
        self._label_alt = label_alt
        self._label_content = label
        self._label_alt_content = label_alt
        self._update_interval = update_interval
        self._menu = menu
        self._callbacks = callbacks
        self._show_alt_label = False

        # Initialize power plans
        self._plans = []
        self._active_guid = None

        build_widget_label(self, self._label_content, self._label_alt_content, self._label_shadow)

        self.register_callback("toggle_menu", self._show_menu)
        self.register_callback("toggle_label", self._toggle_label)
        self.map_callbacks(callbacks)

        if self not in PowerPlanWidget._instances:
            PowerPlanWidget._instances.append(self)

        if update_interval > 0 and PowerPlanWidget._shared_timer is None:
            PowerPlanWidget._shared_timer = QTimer(self)
            PowerPlanWidget._shared_timer.setInterval(update_interval)
            PowerPlanWidget._shared_timer.timeout.connect(PowerPlanWidget._notify_instances)
            PowerPlanWidget._shared_timer.start()
        PowerPlanWidget._notify_instances()

    @classmethod
    def _notify_instances(cls):
        """Fetch power plans and update all instances."""
        if not cls._instances:
            return

        try:
            plans, active_guid = cls._instances[0].get_power_plans()
        except Exception as e:
            logging.error(f"Error fetching power plans: {e}")
            return

        # update each widget using the shared data
        for inst in cls._instances[:]:
            try:
                inst._plans = plans
                inst._active_guid = active_guid

                inst._plans = plans
                inst._active_guid = active_guid
                inst._active_plan_name = "Unknown"
                inst._plan_class_name = "unknown"
                for plan in plans:
                    if active_guid and inst._guids_equal(plan["guid"], active_guid):
                        inst._active_plan_name = plan["name"]
                        inst._plan_class_name = plan["name"].replace(" ", "-").lower()
                        break

                inst._update_label()
            except RuntimeError:
                cls._instances.remove(inst)

    def _load_power_plans(self):
        """Load available power plans."""
        try:
            self._plans, self._active_guid = self.get_power_plans()

            self._active_plan_name = "Unknown"
            self._plan_class_name = "unknown"

            for plan in self._plans:
                if self._active_guid and self._guids_equal(plan["guid"], self._active_guid):
                    self._active_plan_name = plan["name"]
                    self._plan_class_name = plan["name"].replace(" ", "-").lower()
                    break

        except Exception as e:
            logging.error(f"Error loading power plans: {e}")
            self._active_plan_name = "Unknown"
            self._plan_class_name = "unknown"

    def _update_label(self):
        """Update the label with the current power plan name."""

        # active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_widgets = self._widgets
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        active_label_content = active_label_content.format(active_plan=self._active_plan_name)

        for label in iterate_label_as_parts(
            self, active_widgets, active_label_content, "alt" if self._show_alt_label else ""
        ):
            label.setProperty("class", label.property("class") + " " + self._plan_class_name)
            label.setStyleSheet("")

    def _toggle_label(self):
        """Toggle between main and alt labels."""
        self._show_alt_label = not self._show_alt_label
        # for widget in self._widgets:
        #     widget.setVisible(not self._show_alt_label)
        # for widget in self._widgets_alt:
        #     widget.setVisible(self._show_alt_label)
        self._update_label()

    def _show_menu(self):
        """Show the power plan selection popup."""

        self._load_power_plans()
        self._popup_menu = PopupWidget(
            self,
            self._menu["blur"],
            self._menu["round_corners"],
            self._menu["round_corners_type"],
            self._menu["border_color"],
        )
        self._popup_menu.setProperty("class", "power-plan-menu")

        # Create main layout for popup
        main_layout = BaseVBoxLayout()

        # Create frame to contain all buttons
        frame = BaseFrame(class_name="menu-content")
        frame_layout = BaseVBoxLayout()

        # Add power plan buttons to frame layout
        for plan in self._plans:
            btn = QPushButton(plan["name"])
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            if self._active_guid and self._guids_equal(plan["guid"], self._active_guid):
                btn.setProperty("class", "button active")
                btn.setText(plan["name"])
            else:
                btn.setProperty("class", "button")

            btn.clicked.connect(lambda checked, guid=plan["guid"], name=plan["name"]: self._change_plan(guid, name))

            frame_layout.addWidget(btn)

        frame.setLayout(frame_layout)
        main_layout.addWidget(frame)

        self._popup_menu.setLayout(main_layout)
        self._popup_menu.adjustSize()
        self._popup_menu.setPosition(
            self._menu["alignment"],
            self._menu["direction"],
            self._menu["offset_left"],
            self._menu["offset_top"],
        )
        self._popup_menu.show()

    def _change_plan(self, guid, name):
        """Change the active power plan."""

        self._popup_menu.hide()
        try:
            result = self.set_power_plan(guid)
            if not result == 0:
                logging.error(f"Failed to change power plan. Error code: {result}")
                return

            self._active_plan_name = name
            self._plan_class_name = name.replace(" ", "-").lower()
            try:
                PowerPlanWidget._notify_instances()
            except Exception as e:
                logging.warning(f"Failed to notify instances after changing power plan: {e}")
        except Exception as e:
            logging.error(f"Error changing power plan: {e}")

    def _guids_equal(self, guid1, guid2):
        """Compare two GUIDs for equality."""
        try:
            return ctypes.string_at(ctypes.byref(guid1), ctypes.sizeof(GUID)) == ctypes.string_at(
                ctypes.byref(guid2), ctypes.sizeof(GUID)
            )
        except:
            return False

    def get_power_plans(self):
        """Get all available power plans and the currently active one."""

        index = 0
        plans = []

        while True:
            guid_buf = (ctypes.c_ubyte * 16)()
            size = wintypes.DWORD(16)
            res = PowerEnumerate(None, None, None, 16, index, guid_buf, ctypes.byref(size))
            if res != 0:
                break

            guid = GUID.from_buffer_copy(guid_buf)

            # Get friendly name
            name_buf = (ctypes.c_ubyte * 1024)()
            name_size = wintypes.DWORD(1024)
            PowerReadFriendlyName(None, ctypes.byref(guid), None, None, name_buf, ctypes.byref(name_size))
            name = bytes(name_buf[: name_size.value]).decode("utf-16", errors="ignore").strip("\x00")

            plans.append({"guid": guid, "name": name})
            index += 1

        # Get active scheme
        active_ptr = ctypes.POINTER(GUID)()
        PowerGetActiveScheme(None, ctypes.byref(active_ptr))
        active_guid = active_ptr.contents if active_ptr else None

        return plans, active_guid

    def set_power_plan(self, guid):
        """Set the active power plan."""
        return PowerSetActiveScheme(None, ctypes.byref(guid))
