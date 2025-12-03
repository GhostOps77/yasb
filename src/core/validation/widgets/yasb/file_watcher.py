DEFAULTS = {
    "class_name": "",
    "listen_paths": [
        {
            "patterns": None,
            "ignore_patterns": [],
            "ignore_directories": True,
            "read_file_contents": False,
            "read_max_bytes": 65536,
            "labels": {
                "file": {
                    "created": "",
                    "modified": "",
                    "deleted": "",
                    "moved": "",
                },
                "folder": {
                    "created": "",
                    "modified": "",
                    "deleted": "",
                    "moved": "",
                },
            },
        }
    ],
    "label_max_length": None,
    "clear_labels_after_interval": None,
    "read_max_bytes": 65536,
    # "animation": {"enabled": True, "type": "fadeInOut", "duration": 200},
    # "callbacks": {
    #     "on_left": "toggle_label",
    #     "on_middle": "do_nothing",
    #     "on_right": "do_nothing",
    # },
}


VALIDATION_SCHEMA = {
    "class_name": {"type": "string", "required": False, "default": DEFAULTS["class_name"]},
    "listen_paths": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "directory": {"type": "string", "required": True},
                "patterns": {
                    "type": "list",
                    "nullable": True,
                    "schema": {"type": "string"},
                    "default": DEFAULTS["listen_paths"][0]["patterns"],
                },
                "ignore_patterns": {
                    "type": "list",
                    "schema": {"type": "string"},
                    "default": DEFAULTS["listen_paths"][0]["ignore_patterns"],
                },
                "ignore_directories": {
                    "type": "boolean",
                    "default": DEFAULTS["listen_paths"][0]["ignore_directories"],
                },
                "read_file_contents": {
                    "type": "boolean",
                    "default": DEFAULTS["listen_paths"][0]["read_file_contents"],
                },
                "read_max_bytes": {
                    "type": "integer",
                    "min": 1,
                    "default": DEFAULTS["listen_paths"][0]["read_max_bytes"],
                },
                "labels": {
                    "type": "dict",
                    "default": DEFAULTS["listen_paths"][0]["labels"],
                    "schema": {
                        "file": {
                            "type": "dict",
                            "default": DEFAULTS["listen_paths"][0]["labels"]["file"],
                            "schema": {
                                "created": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["file"]["created"],
                                },
                                "modified": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["file"]["modified"],
                                },
                                "deleted": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["file"]["deleted"],
                                },
                                "moved": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["file"]["moved"],
                                },
                            },
                        },
                        "folder": {
                            "type": "dict",
                            "default": DEFAULTS["listen_paths"][0]["labels"]["folder"],
                            "schema": {
                                "created": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["folder"]["created"],
                                },
                                "modified": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["folder"]["modified"],
                                },
                                "deleted": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["folder"]["deleted"],
                                },
                                "moved": {
                                    "type": "string",
                                    "default": DEFAULTS["listen_paths"][0]["labels"]["folder"]["moved"],
                                },
                            },
                        },
                    },
                    # "description": "Templates for labels; templates may include {action}, {path}, {name}, {content}"
                },
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
