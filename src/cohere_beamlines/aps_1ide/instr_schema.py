"""aps_1ide InstrTab schema. See aps_34idc/instr_schema.py for the format reference."""

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
        {
            'key': 'detector', 'label': 'detector',
            'type': 'choice', 'auto_choices': 'detector',
            'description': 'Detector hardware used for this experiment.',
        },
        {'key': 'energy', 'label': 'energy', 'unit': 'keV', 'type': 'float',
         'description': 'Incident beam energy. Values below 1000 are treated as keV, otherwise eV.'},
        {'key': 'detdist', 'label': 'detector distance', 'unit': 'mm',
         'type': 'float',
         'description': 'Sample-to-detector distance.'},
        {'key': 'vff_eta_offset', 'label': 'vff_eta offset',
         'type': 'float',
         'description': 'Offset added to vff_eta.'},
        {'key': 'vff_r_offset', 'label': 'vff_r offset', 'unit': 'm',
         'type': 'float',
         'description': 'Offset added to vff_r (after mm→m conversion).'},
    ],
    'spec': [
        {'key': 'aero', 'label': 'aero', 'unit': 'deg', 'type': 'float',
         'description': 'AeroTech sample motor.'},
        {'key': 'vff_eta', 'label': 'vff_eta', 'type': 'float'},
        {'key': 'vff_r', 'label': 'vff_r', 'unit': 'mm', 'type': 'float'},
        {'key': 'scanmot', 'label': 'scan motor', 'type': 'choice',
         'choices': ['aero'],
         'description': 'Motor that defines the scan steps. Pick a listed '
                        'motor or use (custom...) to type a different name.'},
    ],
}

SPEC_DRIVERS = ('specfile',)
