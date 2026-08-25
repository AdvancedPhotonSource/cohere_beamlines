"""aps_20ide InstrTab schema. See aps_34idc/instr_schema.py for the format reference."""

INSTR_FIELDS = {
    'general': [
        {
            'key': 'data_dir', 'label': 'data directory', 'type': 'dir',
            'description': 'Directory containing the raw detector frames and metadata.',
        },
        {
            'key': 'darkfield_filename', 'label': 'darkfield file', 'type': 'file',
            'description': 'Dark-field reference image (subtracted from frames).',
        },
        {
            'key': 'whitefield_filename', 'label': 'whitefield file', 'type': 'file',
            'description': 'White-field reference image (flat-field correction).',
        },
        {
            'key': 'Imult', 'label': 'Imult', 'type': 'float',
            'description': 'Intensity multiplier applied to every frame.',
        },
        {
            'key': 'detector', 'label': 'detector',
            'type': 'choice', 'auto_choices': 'detector',
            'description': 'Detector hardware used for this experiment.',
        },
        {
            'key': 'remove_band_background',
            'label': 'remove band background', 'type': 'bool',
            'description': 'Enable horizontal band (row-wise) background '
                           'subtraction.',
        },
        {
            'key': 'rbb_smooth_sigma',
            'label': 'rbb smooth sigma', 'type': 'float',
            'description': 'Gaussian smoothing width for the row profile. '
                           'Higher = smoother background. Default 50.',
        },
        {
            'key': 'rbb_robust', 'label': 'rbb robust', 'type': 'bool',
            'description': 'If on, use the median across columns '
                           '(robust to bright objects). Off = use the mean.',
        },
        {'key': 'scan_step', 'label': 'scan_step', 'unit': 'deg',
         'type': 'float',
         'description': 'scan step size, typically calculated from metadata.'},
    ],
    'spec': [
        {'key': 'energy', 'label': 'energy', 'unit': 'keV', 'type': 'float',
         'description': 'Incident beam energy. Values below 1000 are treated as keV, otherwise eV.'},
        {'key': 'DetX', 'label': 'DetX', 'unit': 'mm', 'type': 'float',
         'description': 'Detector X position.'},
        {'key': 'DetY', 'label': 'DetY', 'unit': 'mm', 'type': 'float',
         'description': 'Detector Y position.'},
        {'key': 'DetZ', 'label': 'DetZ', 'unit': 'mm', 'type': 'float',
         'description': 'Detector Z position (sample-to-detector distance).'},
        {'key': 'samRy', 'label': 'samRy', 'unit': 'deg', 'type': 'float',
         'description': 'Sample rotation motor (LabMotion).'},
        {'key': 'scanmot', 'label': 'scan motor', 'type': 'choice',
         'choices': ['samRy'],
         'description': 'Motor that defines the scan steps. Pick a listed '
                        'motor or use (custom...) to type a different name.'},
    ],
}

SPEC_DRIVERS = ('data_dir',)

def get_config_schema():
    return INSTR_FIELDS