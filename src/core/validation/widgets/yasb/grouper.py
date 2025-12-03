DEFAULTS = {
    "class_name": "grouper",
    "widgets": [],
    "hide_empty": False,
}

VALIDATION_SCHEMA = {
    "class_name": {"type": "string", "default": DEFAULTS["class_name"]},
    "widgets": {
        "type": "list",
        "default": DEFAULTS["widgets"],
        "schema": {
            "type": "string",
            "required": False,
        },
    },
    "hide_empty": {
        "type": "boolean",
        "required": False,
        "default": DEFAULTS["hide_empty"],
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
