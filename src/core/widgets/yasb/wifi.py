import logging
import socket
from typing import Any

from PyQt6.QtWidgets import QLabel
from winrt.windows.networking.connectivity import NetworkConnectivityLevel, NetworkInformation

from core.utils.utilities import iterate_label_as_parts
from core.utils.widgets.wifi.wifi_managers import NetworkInfo
from core.utils.widgets.wifi.wifi_widgets import WifiMenu
from core.validation.widgets.yasb.wifi import VALIDATION_SCHEMA
from core.widgets.base import BaseWidget

logger = logging.getLogger("wifi_widget")


class WifiWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA
    _networks_cache: list[NetworkInfo] = []

    def __init__(
        self,
        label: str,
        label_alt: str,
        update_interval: int,
        class_name: str,
        wifi_icons: list[str],
        ethernet_label: str,
        ethernet_label_alt: str,
        ethernet_icon: str,
        get_exact_wifi_strength: bool,
        hide_if_ethernet: bool,
        animation: dict[str, str],
        callbacks: dict[str, str],
        menu_config: dict[str, Any],
        **kwargs,
    ):
        super().__init__(update_interval, class_name=f"wifi-widget {class_name}", **kwargs)
        self._wifi_menu = WifiMenu(self, menu_config)

        self._wifi_icons = wifi_icons
        self._ethernet_icon = ethernet_icon

        self._show_alt_label = False
        self._ethernet_active = False
        self._label_content = label
        self._label_alt_content = label_alt
        self._ethernet_label_content = ethernet_label
        self._ethernet_label_alt_content = ethernet_label_alt
        self._get_exact_wifi_strength = get_exact_wifi_strength
        self._hide_if_ethernet = hide_if_ethernet
        self._animation = animation

        self._create_dynamically_label(self._label_content, self._label_alt_content)
        self._create_dynamically_label(self._ethernet_label_content, self._ethernet_label_alt_content, is_ethernet=True)

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("update_label", self._update_label)
        self.register_callback("toggle_menu", self._wifi_menu.show_menu)
        self.register_callback("timer", self._update_label)
        self.map_callbacks(callbacks)

        self.start_timer()

    def _display_correct_label(self):
        for widget in self._widgets:
            widget.setVisible(not self._ethernet_active)

        for widget in self._widgets_ethernet:
            widget.setVisible(self._ethernet_active)

    def _toggle_label(self):
        self._animate()
        self._show_alt_label = not self._show_alt_label
        self._update_label()

    def _create_dynamically_label(self, content: str, content_alt: str, is_ethernet: bool = False):
        def process_content(content: str, is_alt: bool = False, is_ethernet: bool = False) -> list[QLabel]:
            # Filters out empty parts before entering the loop
            widgets: list[QLabel] = []

            for label in iterate_label_as_parts(self, widgets, content, "alt" if is_alt else ""):
                if is_ethernet:
                    label.hide()
                else:
                    label.show()

            return widgets

        if is_ethernet:
            self._widgets_ethernet = process_content(content, is_ethernet=True)
            # self._widgets_ethernet_alt = process_content(content_alt, is_alt=True, is_ethernet=True)
            self._widgets_ethernet_alt = self._widgets_ethernet
        else:
            self._widgets = process_content(content)
            # self._widgets_alt = process_content(content_alt, is_alt=True)
            self._widgets_alt = self._widgets

    def _update_label(self):
        try:
            connection_info = NetworkInformation.get_internet_connection_profile()
            ip_addr = socket.gethostbyname(socket.gethostname())
            if connection_info is None or connection_info.is_wlan_connection_profile:  # type: ignore
                was_ethernet = self._ethernet_active
                self._ethernet_active = False
                if was_ethernet and self._hide_if_ethernet:
                    self.show()

                # NOTE: Optionally get the exact wifi strength from winapi (won't work if location services are disabled)
                winapi_connection_info: NetworkInfo | None = None
                if self._get_exact_wifi_strength:
                    winapi_connection_info = self._wifi_menu.wifi_manager.get_current_connection()

                if winapi_connection_info:
                    wifi_strength = winapi_connection_info.quality
                else:
                    wifi_strength = min(self._get_wifi_strength_safe(), 4) * 25
                wifi_icon = self._get_wifi_icon(wifi_strength)
                wifi_name = self._get_wifi_name_safe()
            else:
                self._ethernet_active = True
                if self._hide_if_ethernet:
                    self.hide()
                    return
                wifi_icon = self._ethernet_icon
                wifi_name = "Ethernet"
                wifi_strength = "N/A"

        except Exception as e:
            logger.error(f"Error in wifi widget update: {e}")
            ip_addr = "N/A"
            wifi_icon = wifi_name = wifi_strength = "N/A"

        if self._ethernet_active:
            # active_widgets = self._widgets_ethernet_alt if self._show_alt_label else self._widgets_ethernet
            active_widgets = self._widgets_ethernet
            active_label_content = (
                self._ethernet_label_alt_content if self._show_alt_label else self._ethernet_label_content
            )
        else:
            # active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
            active_widgets = self._widgets
            active_label_content = self._label_alt_content if self._show_alt_label else self._label_content

        active_label_content = active_label_content.format(
            wifi_icon=wifi_icon,
            wifi_name=wifi_name,
            wifi_strength=wifi_strength,
            ip_addr=ip_addr,
        )

        for _ in iterate_label_as_parts(
            active_widgets, active_label_content, "label alt" if self._show_alt_label else "label"
        ):
            pass

        self._display_correct_label()

    def _get_wifi_strength_safe(self) -> int:
        """Get the WiFi signal bars safely, not requiring location permissions"""
        connections = NetworkInformation.get_connection_profiles()
        for connection in connections:
            if connection.get_network_connectivity_level() == NetworkConnectivityLevel.INTERNET_ACCESS:
                signal_strength = connection.get_signal_bars()
                if signal_strength is not None:
                    return signal_strength
        return 0

    def _get_wifi_name_safe(self) -> str:
        """Get the WiFi name safely, not requiring location permissions"""
        connections = NetworkInformation.get_connection_profiles()
        for connection in connections:
            if connection.get_network_connectivity_level() == NetworkConnectivityLevel.INTERNET_ACCESS:
                return connection.profile_name
        return "Disconnected"

    def _get_wifi_icon(self, strength: int) -> str:
        if strength >= 80:
            bars = 4
        elif strength >= 60:
            bars = 3
        elif strength >= 40:
            bars = 2
        elif strength >= 20:
            bars = 1
        else:
            bars = 0
        return self._wifi_icons[bars]
