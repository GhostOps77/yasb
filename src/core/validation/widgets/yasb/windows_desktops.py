DEFAULTS = {
    "label_workspace_btn": "{index}",
    "label_workspace_active_btn": "{index}",
    "switch_workspace_animation": True,
    "animation": False,
}
VALIDATION_SCHEMA = {
    "label_workspace_btn": {
        "type": "string",
        "default": DEFAULTS["label_workspace_btn"],
    },
    "label_workspace_active_btn": {
        "type": "string",
        "default": DEFAULTS["label_workspace_active_btn"],
    },
    "switch_workspace_animation": {
        "type": "boolean",
        "required": False,
        "default": DEFAULTS["switch_workspace_animation"],
    },
    "animation": {
        "type": "boolean",
        "required": False,
        "default": DEFAULTS["animation"],
    },
    "btn_shadow": {
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
}
