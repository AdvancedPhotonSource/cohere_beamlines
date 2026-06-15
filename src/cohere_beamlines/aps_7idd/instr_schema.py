"""aps_7idd InstrTab schema. See aps_34idc/instr_schema.py for the format reference."""

INSTR_FIELDS = {
    'general': [
        {
            'key': 'specfile', 'label': 'spec file', 'type': 'file',
            'description': 'SPEC log file with the scan metadata.',
        },
        {
            'key': 'data_dir', 'label': 'data directory', 'type': 'dir',
            'description': 'Directory containing the raw detector frames.',
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
    ],
    'spec': [
        {'key': 'energy', 'label': 'energy', 'unit': 'keV', 'type': 'float',
         'description': 'Incident beam energy. Values below 1000 are treated as keV, otherwise eV.'},
        {'key': 'yaw', 'label': 'yaw', 'unit': 'deg', 'type': 'float',
         'description': 'Yaw detector motor.'},
        {'key': 'pitch', 'label': 'pitch', 'unit': 'deg', 'type': 'float',
         'description': 'Pitch detector motor.'},
        {'key': 'radius', 'label': 'Radius', 'unit': 'mm', 'type': 'float',
         'description': 'Sample-to-detector distance.'},
        {'key': 'roi', 'label': 'detector ROI',
         'placeholder': 'e.g., [0, 256, 0, 256]',
         'description': 'Detector ROI [y0, height, x0, width].'},
        {'key': 'wedge', 'label': 'wedge', 'unit': 'deg', 'type': 'float',
         'description': 'Fixed wedge angle (typically 10 deg).'},
        {'key': 'chi', 'label': 'chi', 'unit': 'deg', 'type': 'float'},
        {'key': 'th', 'label': 'theta', 'unit': 'deg', 'type': 'float',
         'description': 'ThetaN sample motor.'},
        {'key': 'phi', 'label': 'phi', 'unit': 'deg', 'type': 'float'},
        {'key': 'scanmot', 'label': 'scan motor', 'type': 'choice',
         'choices': ['wedge', 'chi', 'th', 'phi'],
         'description': 'Motor that defines the scan steps. Pick a listed '
                        'motor or use (custom...) to type a different name.'},
        {'key': 'detector', 'label': 'detector',
         'type': 'choice', 'auto_choices': 'detector',
         'description': 'Detector hardware used for this experiment.'},
    ],
}

SPEC_DRIVERS = ('specfile',)
