DEFAULTS = {
    "label": "\ue71a",
    "power_menu": True,
    "system_menu": True,
    "blur": False,
    "round_corners": True,
    "round_corners_type": "normal",
    "border_color": "System",
    "alignment": "left",
    "direction": "down",
    "distance": 6,  # deprecated
    "offset_top": 6,
    "offset_left": 0,
    "menu_labels": {
        "shutdown": "Shutdown",
        "restart": "Restart",
        "hibernate": "Hibernate",
        "logout": "Logout",
        "lock": "Lock",
        "sleep": "Sleep",
        "system": "System Settings",
        "about": "About This PC",
        "task_manager": "Task Manager",
    },
    "animation": {"enabled": True, "type": "fadeInOut", "duration": 200},
    "callbacks": {"on_left": "toggle_menu"},
}

VALIDATION_SCHEMA = {
    "label": {"type": "string", "default": DEFAULTS["label"]},
    "menu_list": {
        "required": False,
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {"title": {"type": "string"}, "path": {"type": "string"}},
        },
    },
    "power_menu": {
        "type": "boolean",
        "default": DEFAULTS["power_menu"],
        "required": False,
    },
    "system_menu": {
        "type": "boolean",
        "default": DEFAULTS["system_menu"],
        "required": False,
    },
    "blur": {"type": "boolean", "default": DEFAULTS["blur"], "required": False},
    "round_corners": {
        "type": "boolean",
        "default": DEFAULTS["round_corners"],
        "required": False,
    },
    "round_corners_type": {
        "type": "string",
        "default": DEFAULTS["round_corners_type"],
        "required": False,
    },
    "border_color": {
        "type": "string",
        "default": DEFAULTS["border_color"],
        "required": False,
    },
    "alignment": {
        "type": "string",
        "default": DEFAULTS["alignment"],
        "required": False,
    },
    "direction": {
        "type": "string",
        "default": DEFAULTS["direction"],
        "required": False,
    },
    "distance": {"type": "integer", "default": DEFAULTS["distance"], "required": False},
    "offset_top": {
        "type": "integer",
        "default": DEFAULTS["offset_top"],
        "required": False,
    },
    "offset_left": {
        "type": "integer",
        "default": DEFAULTS["offset_left"],
        "required": False,
    },
    "menu_labels": {
        "type": "dict",
        "required": False,
        "schema": {
            "shutdown": {
                "type": "string",
                "default": DEFAULTS["menu_labels"]["shutdown"],
            },
            "restart": {
                "type": "string",
                "default": DEFAULTS["menu_labels"]["restart"],
            },
            "hibernate": {
                "type": "string",
                "default": DEFAULTS["menu_labels"]["hibernate"],
            },
            "logout": {"type": "string", "default": DEFAULTS["menu_labels"]["logout"]},
            "lock": {"type": "string", "default": DEFAULTS["menu_labels"]["lock"]},
            "sleep": {"type": "string", "default": DEFAULTS["menu_labels"]["sleep"]},
            "system": {"type": "string", "default": DEFAULTS["menu_labels"]["system"]},
            "about": {"type": "string", "default": DEFAULTS["menu_labels"]["about"]},
            "task_manager": {
                "type": "string",
                "default": DEFAULTS["menu_labels"]["task_manager"],
            },
        },
        "default": DEFAULTS["menu_labels"],
    },
    "animation": {
        "type": "dict",
        "required": False,
        "schema": {
            "enabled": {"type": "boolean", "default": DEFAULTS["animation"]["enabled"]},
            "type": {"type": "string", "default": DEFAULTS["animation"]["type"]},
            "duration": {
                "type": "integer",
                "default": DEFAULTS["animation"]["duration"],
            },
        },
        "default": DEFAULTS["animation"],
    },
    "label_shadow": {
        "type": "dict",
        "required": False,
        "schema": {
            "enabled": {"type": "boolean", "default": False},
            "color": {"type": "string", "default": "black"},
            "offset": {"type": "list", "default": [1, 1]},
            "radius": {"type": "integer", "default": 3},
        },
        "default": {"enabled": False, "color": "black", "offset": [1, 1], "radius": 3},
    },
    "container_shadow": {
        "type": "dict",
        "required": False,
        "schema": {
            "enabled": {"type": "boolean", "default": False},
            "color": {"type": "string", "default": "black"},
            "offset": {"type": "list", "default": [1, 1]},
            "radius": {"type": "integer", "default": 3},
        },
        "default": {"enabled": False, "color": "black", "offset": [1, 1], "radius": 3},
    },
    "callbacks": {
        "required": False,
        "type": "dict",
        "schema": {"on_left": {"type": "string", "default": DEFAULTS["callbacks"]["on_left"]}},
        "default": DEFAULTS["callbacks"],
    },
}
