DEFAULTS = {
    'label': '{title}',
    'label_alt': '{artist} - {title}',
    'animation': {
        'enabled': True,
        'type': 'fadeInOut',
        'duration': 200
    },
    'media_menu': {
        'blur': True,
        'round_corners': True,
        'round_corners_type': 'normal',
        'border_color': 'System',
        'alignment': 'right',
        'direction': 'down',
        'offset_top': 6,
        'offset_left': 0,
        'thumbnail_size': 100,
        'thumbnail_corner_radius': 8,
        'max_title_size': 150,
        'max_artist_size': 40,
        'show_source': True
    },
    'media_menu_icons': {
        'play': '\ue768',
        'pause': '\ue769',
        'prev_track': '\ue892',
        'next_track': '\ue893'
    },
    'container_padding': {'top': 0, 'left': 0, 'bottom': 0, 'right': 0},
    'callbacks': {
        'on_left': 'toggle_label',
        'on_middle': 'do_nothing',
        'on_right': 'do_nothing'
    }
}

VALIDATION_SCHEMA = {
    'label': {
        'type': 'string',
        'default': DEFAULTS['label']
    },
    'label_alt': {
        'type': 'string',
        'default': DEFAULTS['label_alt']
    },
    'hide_empty': {
        'type': 'boolean',
        'default': False
    },
    'animation': {
        'type': 'dict',
        'required': False,
        'schema': {
            'enabled': {
                'type': 'boolean',
                'default': DEFAULTS['animation']['enabled']
            },
            'type': {
                'type': 'string',
                'default': DEFAULTS['animation']['type']
            },
            'duration': {
                'type': 'integer',
                'default': DEFAULTS['animation']['duration']
            }
        },
        'default': DEFAULTS['animation']
    },
    'media_menu': {
        'type': 'dict',
        'required': False,
        'schema': {
            'blur': {
                'type': 'boolean',
                'default': DEFAULTS['media_menu']['blur']
            },
            'round_corners': {
                'type': 'boolean',
                'default': DEFAULTS['media_menu']['round_corners']
            },
            'round_corners_type': {
                'type': 'string',
                'default': DEFAULTS['media_menu']['round_corners_type']
            },
            'border_color': {
                'type': 'string',
                'default': DEFAULTS['media_menu']['border_color']
            },
            'alignment': {
                'type': 'string',
                'default': DEFAULTS['media_menu']['alignment'],
                'allowed': ['left', 'right', 'center']
            },
            'direction': {
                'type': 'string',
                'default': DEFAULTS['media_menu']['direction'],
                'allowed': ['up', 'down']
            },
            'offset_top': {
                'type': 'integer',
                'default': DEFAULTS['media_menu']['offset_top']
            },
            'offset_left': {
                'type': 'integer',
                'default': DEFAULTS['media_menu']['offset_left']
            },
            'thumbnail_size': {
                'type': 'integer',
                'default': DEFAULTS['media_menu']['thumbnail_size']
            },
            'thumbnail_corner_radius': {
                'type': 'integer',
                'default': DEFAULTS['media_menu']['thumbnail_corner_radius']
            },
            'max_title_size': {
                'type': 'integer',
                'default': DEFAULTS['media_menu']['max_title_size']
            },
            'max_artist_size': {
                'type': 'integer',
                'default': DEFAULTS['media_menu']['max_artist_size']
            },
            'show_source': {
                'type': 'boolean',
                'default': DEFAULTS['media_menu']['show_source']
            }
        },
        'default': DEFAULTS['media_menu']
    },
    'media_menu_icons': {
        'type': 'dict',
        'required': False,
        'schema': {
            'play': {
                'type': 'string',
                'default': DEFAULTS['media_menu_icons']['play'],
            },
            'pause': {
                'type': 'string',
                'default': DEFAULTS['media_menu_icons']['pause'],
            },
            'prev_track': {
                'type': 'string',
                'default': DEFAULTS['media_menu_icons']['prev_track'],
            },
            'next_track': {
                'type': 'string',
                'default': DEFAULTS['media_menu_icons']['next_track'],
            }
        },
        'default': DEFAULTS['media_menu_icons']
    },
    'label_shadow': {
        'type': 'dict',
        'required': False,
        'schema': {
            'enabled': {'type': 'boolean', 'default': False},
            'color': {'type': 'string', 'default': 'black'},
            'offset': {'type': 'list', 'default': [1, 1]},
            'radius': {'type': 'integer', 'default': 3},
        },
        'default': {'enabled': False, 'color': 'black', 'offset': [1, 1], 'radius': 3}
    },
    'container_shadow': {
        'type': 'dict',
        'required': False,
        'schema': {
            'enabled': {'type': 'boolean', 'default': False},
            'color': {'type': 'string', 'default': 'black'},
            'offset': {'type': 'list', 'default': [1, 1]},
            'radius': {'type': 'integer', 'default': 3},
        },
        'default': {'enabled': False, 'color': 'black', 'offset': [1, 1], 'radius': 3}
    },
    'container_padding': {
        'type': 'dict',
        'required': False,
        'schema': {
            'top': {
                'type': 'integer',
                'default': DEFAULTS['container_padding']['top']
            },
            'left': {
                'type': 'integer',
                'default': DEFAULTS['container_padding']['left']
            },
            'bottom': {
                'type': 'integer',
                'default': DEFAULTS['container_padding']['bottom']
            },
            'right': {
                'type': 'integer',
                'default': DEFAULTS['container_padding']['right']
            }
        },
        'default': DEFAULTS['container_padding']
    },
    'callbacks': {
        'type': 'dict',
        'schema': {
            'on_left': {
                'type': 'string',
                'default': DEFAULTS['callbacks']['on_left'],
            },
            'on_middle': {
                'type': 'string',
                'default': DEFAULTS['callbacks']['on_middle'],
            },
            'on_right': {
                'type': 'string',
                'default': DEFAULTS['callbacks']['on_right'],
            }
        },
        'default': DEFAULTS['callbacks']
    },
    'max_field_size': {
        'type': 'dict',
        'schema': {
            'label': {
                'type': 'integer',
                'default': 15,
                'min': 0,
                'max': 200
            },
            'label_alt': {
                'type': 'integer',
                'default': 30,
                'min': 0,
                'max': 200
            }         
        }
    },
    'show_thumbnail': {
        'type': 'boolean',
        'default': True
    },
    'controls_only': {
        'type': 'boolean',
        'default': False
    },
    'controls_left': {
        'type': 'boolean',
        'default': True
    },
    'controls_hide': {
        'type': 'boolean',
        'default': False
    },
    'thumbnail_alpha': {
        'type': 'integer',
        'default': 50,
        'min': 0,
        'max': 255
    },
    'thumbnail_padding': {
        'type': 'integer',
        'default': 8,
        'min': 0,
        'max': 200
    },
    'thumbnail_corner_radius': {
        'type': 'integer',
        'default': 0,
        'min': 0,
        'max': 100
    },
    'symmetric_corner_radius': {
        'type': 'boolean',
        'default': False
    },
    'thumbnail_edge_fade': {
        'type': 'boolean',
        'default': False
    },
    'icons': {
        'type': 'dict',
        'required': False,
        'schema': {
            'prev_track': {
                'type': 'string',
                'default': '\uf048',
            },
            'next_track': {
                'type': 'string',
                'default': '\uf051',
            },
            'play': {
                'type': 'string',
                'default': '\uf04b',
            },
            'pause': {
                'type': 'string',
                'default': '\uf04c',
            },
        },
    }
}