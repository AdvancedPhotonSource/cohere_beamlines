"""`simple` InstrTab schema. See aps_34idc/instr_schema.py for the format reference.

Minimal stub beamline: parse_metadata returns {}, so the spec section
stays empty and the user fills the general fields by hand.
"""
INSTR_FIELDS = [
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
            'key': 'det_roi', 'label': 'detector ROI',
            'placeholder': 'e.g., [0, 256, 0, 256]',
            'description': 'Detector ROI [y0, height, x0, width].',
        },
        {'key': 'scan_step', 'label': 'scan_step', 'unit': 'deg',
         'type': 'float',
         'description': 'scan step size, typically calculated from metadata.'},
        {'key': 'energy', 'label': 'energy', 'unit': 'keV', 'type': 'float',
         'description': 'Incident beam energy. Values below 1000 are treated as keV, otherwise eV.'},
        {'key': 'delta', 'label': 'delta', 'unit': 'deg', 'type': 'float',
         'description': 'Delta detector motor.'},
        {'key': 'gamma', 'label': 'gamma', 'unit': 'deg', 'type': 'float',
         'description': 'Gamma detector motor.'},
        {'key': 'detdist', 'label': 'detector distance', 'unit': 'mm',
         'type': 'float',
         'description': 'Sample-to-detector distance.'},
        {'key': 'th', 'label': 'theta', 'unit': 'deg', 'type': 'float',
         'description': 'Theta sample motor.'},
        {'key': 'chi', 'label': 'chi', 'unit': 'deg', 'type': 'float'},
        {'key': 'phi', 'label': 'phi', 'unit': 'deg', 'type': 'float'},
        {'key': 'scanmot', 'label': 'scan motor', 'type': 'choice',
         'choices': ['th', 'chi', 'phi', 'en'],
         'description': 'Motor that defines the scan steps. Pick a listed '
                        'motor or use (custom...) to type a different name.'},
        {'key': 'detector', 'label': 'detector',
         'type': 'choice', 'auto_choices': 'detector',
         'description': 'Detector hardware used for this experiment.'},
    ]

SPEC_DRIVERS = ()

def get_config_schema():
    return INSTR_FIELDS