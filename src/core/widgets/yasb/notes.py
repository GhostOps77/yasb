import json
import logging
import os
import re
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QWidget,
)

from core.config import HOME_CONFIGURATION_DIR
from core.utils.utilities import PopupWidget, build_widget_label, iterate_label_as_parts
from core.validation.widgets.yasb.notes import VALIDATION_SCHEMA
from core.widgets.base import BaseHBoxLayout, BaseLabel, BasePushButton, BaseVBoxLayout, BaseWidget
from settings import DEBUG


class NotesWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA
    _instances = []

    def __init__(
        self,
        label: str,
        label_alt: str,
        class_name: str,
        animation: dict,
        menu: dict,
        icons: dict,
        **kwargs,
    ):
        super().__init__(class_name=f"notes-widget {class_name}", **kwargs)
        NotesWidget._instances.append(self)

        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt
        self._animation = animation
        self._menu_config = menu
        self._icons = icons

        self._notes_file = os.path.join(HOME_CONFIGURATION_DIR, "notes.json")
        self._notes = self._load_notes()

        build_widget_label(self, self._label_content, self._label_alt_content)

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("toggle_menu", self._toggle_menu)
        self.register_callback("update_label", self._update_label)
        self.register_callback("timer", self._update_label)

        self._update_label()

    def __del__(self):
        # Remove instance on deletion
        try:
            self._instances.remove(self)
        except ValueError:
            pass

    @classmethod
    def update_all(cls):
        """Update all instances of NotesWidget"""
        for instance in cls._instances:
            instance._notes = instance._load_notes()
            instance._update_label()

    def _toggle_label(self):
        self._animate()
        self._show_alt_label = not self._show_alt_label
        # for widget in self._widgets:
        #     widget.setVisible(not self._show_alt_label)
        # for widget in self._widgets_alt:
        #     widget.setVisible(self._show_alt_label)
        self._update_label()

    def _toggle_menu(self):
        self._animate()
        self._show_menu()

    def _update_label(self):
        notes_count = len(self._notes)

        # active_widgets = self._widgets_alt if self._show_alt_label else self._widgets
        active_widgets = self._widgets
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        active_label_content = active_label_content.format(count=notes_count)

        for _ in iterate_label_as_parts(active_widgets, active_label_content, layout=self._widget_container_layout):
            pass

    def _show_menu(self):
        self._menu = PopupWidget(
            self,
            self._menu_config["blur"],
            self._menu_config["round_corners"],
            self._menu_config["round_corners_type"],
            self._menu_config["border_color"],
        )
        self._menu.setProperty("class", "notes-menu")

        # Create main layout
        main_layout = BaseVBoxLayout(self._menu)

        # Add text input area with button row - MOVED TO TOP
        input_container = QWidget()
        input_layout = BaseVBoxLayout(input_container, spacing=5, paddings=8)

        # Text input field
        self._note_input = NoteTextEdit(self)
        self._note_input.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self._note_input.setPlaceholderText("Type your note here...")
        self._note_input.setProperty("class", "note-input")
        input_layout.addWidget(self._note_input)

        # Button row
        button_container = QWidget()
        button_layout = BaseHBoxLayout(button_container, spacing=5)

        # Add Note button
        self.add_button = BasePushButton("Add Note", class_name="add-button", on_click=self._add_note_from_input)

        # Cancel button (hidden by default)
        self.cancel_button = BasePushButton("Cancel", class_name="cancel-button", on_click=self._cancel_editing)
        self.cancel_button.hide()

        button_layout.addWidgets(self.add_button, self.cancel_button)

        input_layout.addWidget(button_container)
        main_layout.addWidget(input_container)

        # Create scroll area for notes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setProperty("class", "scroll-area")

        # Style the scrollbar
        scroll_area.setViewportMargins(0, 0, -4, 0)
        scroll_area.setStyleSheet(
            """
            QScrollBar:vertical { border: none; background:transparent; width: 4px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
            QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.2); min-height: 10px; border-radius: 2px; }
            QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 0.35); }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { height: 0px; }
        """
        )

        # Create scroll widget and layout
        scroll_widget = QWidget()
        scroll_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        scroll_layout = BaseVBoxLayout(scroll_widget)

        scroll_area.setWidget(scroll_widget)

        # Add notes to the scroll area
        if self._notes:
            for note in self._notes:
                self._add_note_to_menu(note, scroll_layout)

        else:
            # Show empty state
            empty_label = QLabel(f"{self._icons['note']}  No notes yet!")
            empty_label.setProperty("class", "empty-list")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(empty_label)

        main_layout.addWidget(scroll_area)

        # Initialize edit mode tracking
        self._editing_note = None

        self._menu.adjustSize()
        self._menu.setPosition(
            alignment=self._menu_config["alignment"],
            direction=self._menu_config["direction"],
            offset_left=self._menu_config["offset_left"],
            offset_top=self._menu_config["offset_top"],
        )
        self._menu.show()
        self._note_input.setFocus()

    def _add_note_from_input(self):
        """Add a new note or save changes to an existing note"""
        note_text = self._note_input.toPlainText().strip()
        if not note_text:
            return

        note_data = {
            "title": note_text,
            "timestamp": datetime.now().isoformat(),
        }

        if self._editing_note:
            # Update existing note
            try:
                existing_note_idx = self._notes.index(self._editing_note)
                self._notes[existing_note_idx] = note_data
            except ValueError:
                pass

            self._editing_note = None  # Reset edit mode
            self.add_button.setText("Add Note")
            self.cancel_button.hide()
        else:
            # Add new note
            self._notes.insert(0, note_data)

        self._save_notes()
        NotesWidget.update_all()  # Update all widget instances
        self._note_input.clear()

        if hasattr(self, "_menu"):
            self._menu.hide()
            self._show_menu()

    def _add_note_to_menu(self, note, layout):
        container = QWidget()
        container.setProperty("class", "note-item")
        container.setContentsMargins(0, 0, 0, 0)
        container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Main row
        container_layout = BaseHBoxLayout(container, spacing=5, paddings=8)

        # Note icon
        icon_label = BaseLabel(self._icons["note"], class_name="icon")
        container_layout.addWidget(icon_label)

        # Vertical layout for title + date
        text_container = QWidget()
        text_layout = BaseVBoxLayout(text_container, spacing=6)

        # Title
        display_title = re.sub(r"[\n\t\r]+", "", note["title"])
        if len(display_title) > self._menu_config["max_title_size"]:
            display_title = display_title[: self._menu_config["max_title_size"] - 3] + "..."

        title_label = QLabel(display_title)
        title_label.setProperty("class", "title")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        text_layout.addWidget(title_label)

        # Date under title
        if "timestamp" in note and self._menu_config["show_date_time"]:
            try:
                date_str = datetime.fromisoformat(note["timestamp"]).strftime("%Y-%m-%d %H:%M")
                date_label = BaseLabel(date_str, class_name="date")
                text_layout.addWidget(date_label)
            except (ValueError, TypeError):
                pass

        container_layout.addWidget(text_container)

        # Spacer to push buttons to the right
        container_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Create vertical layout for the buttons
        buttons_container = QWidget()
        # Space between buttons
        buttons_layout = BaseVBoxLayout(buttons_container, spacing=5)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the buttons vertically

        # Copy button on top
        copy_button = BasePushButton(
            self._icons["copy"], class_name="copy-button", on_click=lambda: self._copy_note(note)
        )
        buttons_layout.addWidget(copy_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Delete button on bottom
        delete_button = BasePushButton(
            self._icons["delete"], class_name="delete-button", on_click=lambda: self._delete_note(note)
        )
        buttons_layout.addWidget(delete_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Add the buttons container to the main layout
        container_layout.addWidget(buttons_container)

        # Edit on click
        container.mousePressEvent = lambda e: (
            self._edit_note(note) if e.button() == Qt.MouseButton.LeftButton else None
        )

        # Add container to vertical layout
        layout.addWidget(container)

    def _edit_note(self, note):
        """Edit an existing note in the popup menu"""
        # Set editing mode
        self._editing_note = note

        # Load note content into the input field
        self._note_input.setText(note["title"])
        self._note_input.setFocus()

        # Update UI to show we're in edit mode
        self.add_button.setText("Save Changes")
        self.cancel_button.show()

    def _delete_note(self, note):
        """Delete a note"""
        if note not in self._notes:
            return

        self._notes.remove(note)
        self._save_notes()
        NotesWidget.update_all()  # Update all widget instances

        if hasattr(self, "_menu"):
            self._menu.hide()
            self._show_menu()

    def _cancel_editing(self):
        """Cancel editing mode"""
        self._editing_note = None
        self._note_input.clear()
        self.add_button.setText("Add Note")
        self.cancel_button.hide()

    def _copy_note(self, note):
        """Copy note content to clipboard"""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(note["title"])

    def _load_notes(self) -> list[dict]:
        """Load notes from JSON file"""
        try:
            if os.path.exists(self._notes_file):
                if DEBUG:
                    logging.debug(f"Loading notes from {self._notes_file}")

                with open(self._notes_file, encoding="utf-8") as f:
                    return list(json.load(f))

        except Exception as e:
            logging.error(f"Error loading notes: {e}")

        return []

    def _save_notes(self):
        """Save notes to JSON file"""
        try:
            if DEBUG:
                logging.debug(f"Saving notes to {self._notes_file}")

            with open(self._notes_file, "w", encoding="utf-8") as f:
                json.dump(self._notes, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Error saving notes: {e}")


class NoteTextEdit(QTextEdit):
    """
    Custom QTextEdit widget for note input that overrides keyPressEvent.
    Captures Enter/Return key presses to trigger note addition in the parent widget,
    while allowing multiline input using Shift+Enter.
    """

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            parent = self.parent()
            while parent and not hasattr(parent, "_add_note_from_input"):
                parent = parent.parent()

            if parent:
                parent._add_note_from_input()
            event.accept()
        else:
            super().keyPressEvent(event)
