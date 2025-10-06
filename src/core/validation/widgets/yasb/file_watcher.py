DEFAULTS = {
    "listen_paths": [{
        "patterns": None,
        "ignore_patterns": [],
        "ignore_directories": True,
        "read_file_contents": False,
        "read_max_bytes": 65536,
        "labels": {
            "file": {
                "created": "📄 {data.src.name} created",
                "modified": "✏ {data.src.name} modified",
                "deleted": "🗑 {data.src.name} deleted",
                "moved": "➡ {data.src.name} moved {data.dest.name}",
            },
            "folder": {
                "created": "📂 {data.src.name} created",
                "modified": "📂 {data.src.name} modified",
                "deleted": "📂 {data.src.name} deleted",
                "moved": "📂 {data.src.name} moved to {data.dest.name}",
            },
        },
    }],
    "label_max_length": None,
    "clear_labels_after_interval": None,
    "read_max_bytes": 65536,
    # "animation": {"enabled": True, "type": "fadeInOut", "duration": 200},
    "container_padding": {"top": 0, "left": 0, "bottom": 0, "right": 0},
    # "callbacks": {
    #     "on_left": "toggle_label",
    #     "on_middle": "do_nothing",
    #     "on_right": "do_nothing",
    # },
}


VALIDATION_SCHEMA = {
    "listen_paths": {
        "type": "list",
        "required": True,
        "schema": {
            "class-name": {"type": "string", "required": True},
            "directory": {"type": "string", "required": True},
            "patterns": {
                "type": "list",
                "nullable": True,
                "schema": {"type": "string"},
                # "default": None,
                "default": DEFAULTS["listen_paths"][0]['patterns']
            },
            "ignore_patterns": {
                "type": "list",
                "schema": {"type": "string"},
                # "default": [],
                "default": DEFAULTS["listen_paths"][0]['ignore_patterns']
            },
            "ignore_directories": {
                "type": "boolean",
                # "default": True,
                "default": DEFAULTS["listen_paths"][0]['ignore_directories']
            },
            "read_file_contents": {
                "type": "boolean",
                # "default": False,
                "default": DEFAULTS["listen_paths"][0]['read_file_contents']
            },
            "read_max_bytes": {
                "type": "integer",
                "min": 1,
                # "default": 65536,
                "default": DEFAULTS["listen_paths"][0]['read_max_bytes']
            },
            "labels": {
                "type": "dict",
                "default": DEFAULTS["listen_paths"][0]["labels"],
                "schema": {
                    "file": {
                        "type": "dict",
                        "schema": {
                            "created": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["file"]["created"]},
                            "modified": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["file"]["modified"]},
                            "deleted": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["file"]["deleted"]},
                            "moved": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["file"]["moved"]},
                        },
                    },
                    "folder": {
                        "type": "dict",
                        "schema": {
                            "created": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["folder"]["created"]},
                            "modified": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["folder"]["modified"]},
                            "deleted": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["folder"]["deleted"]},
                            "moved": {"type": "string", "default": DEFAULTS['listen_paths'][0]["labels"]["folder"]["moved"]},
                        },
                    },
                },
                # "description": "Templates for labels; templates may include {action}, {path}, {name}, {content}"
            },
        },
    },
    "clear_labels_after_interval": {
        "type": "integer",
        "nullable": True,
        "min": 100,
        "default": DEFAULTS["clear_labels_after_interval"],
    },
    "label_max_length": {
        "type": "integer",
        "nullable": True,
        "default": DEFAULTS["label_max_length"],
        "min": 1,
    },
    # optional single label and alt label for build_widget_label convenience
    # "label": {
    #     "type": "string",
    #     "default": DEFAULTS['label']
    # },
    # "label_alt": {
    #     "type": "string",
    #     "default": DEFAULTS['label_alt']
    # },
    # "animation": {
    #     "type": "dict",
    #     "required": False,
    #     "schema": {
    #         "enabled": {"type": "boolean", "default": DEFAULTS["animation"]["enabled"]},
    #         "type": {"type": "string", "default": DEFAULTS["animation"]["type"]},
    #         "duration": {
    #             "type": "integer",
    #             "default": DEFAULTS["animation"]["duration"],
    #         },
    #     },
    #     "default": DEFAULTS["animation"],
    # },
    "container_padding": {
        "type": "dict",
        "required": False,
        "schema": {
            "top": {"type": "integer", "default": DEFAULTS["container_padding"]["top"]},
            "left": {
                "type": "integer",
                "default": DEFAULTS["container_padding"]["left"],
            },
            "bottom": {
                "type": "integer",
                "default": DEFAULTS["container_padding"]["bottom"],
            },
            "right": {
                "type": "integer",
                "default": DEFAULTS["container_padding"]["right"],
            },
        },
        "default": DEFAULTS["container_padding"],
    },
    # "label_shadow": {
    #     "type": "dict",
    #     "required": False,
    #     "schema": {
    #         "enabled": {"type": "boolean", "default": False},
    #         "color": {"type": "string", "default": "black"},
    #         "offset": {"type": "list", "default": [1, 1]},
    #         "radius": {"type": "integer", "default": 3},
    #     },
    #     "default": {"enabled": False, "color": "black", "offset": [1, 1], "radius": 3},
    # },
    # "container_shadow": {
    #     "type": "dict",
    #     "required": False,
    #     "schema": {
    #         "enabled": {"type": "boolean", "default": False},
    #         "color": {"type": "string", "default": "black"},
    #         "offset": {"type": "list", "default": [1, 1]},
    #         "radius": {"type": "integer", "default": 3},
    #     },
    #     "default": {"enabled": False, "color": "black", "offset": [1, 1], "radius": 3},
    # },
    # "callbacks": {
    #     "type": "dict",
    #     "schema": {
    #         "on_left": {
    #             "type": "string",
    #             "default": DEFAULTS["callbacks"]["on_left"],
    #         },
    #         "on_middle": {
    #             "type": "string",
    #             "default": DEFAULTS["callbacks"]["on_middle"],
    #         },
    #         "on_right": {
    #             "type": "string",
    #             "default": DEFAULTS["callbacks"]["on_right"],
    #         },
    #     },
    #     "default": DEFAULTS["callbacks"],
    # },
}
