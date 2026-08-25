"""esrf_id01 InstrTab schema. See aps_34idc/instr_schema.py for the format reference."""

INSTR_FIELDS = {
    'general': [
        {
            'key': 'detector', 'label': 'detector',
            'type': 'choice', 'auto_choices': 'detector',
            'description': 'Detector hardware used for this experiment.',
        },
        {
            'key': 'h5file', 'label': 'h5 file', 'type': 'file',
            'description': 'HDF5 file containing the scan data and metadata.',
        },
        {'key': 'scan_step', 'label': 'scan_step', 'unit': 'deg',
         'type': 'float',
         'description': 'scan step size, typically calculated from metadata.'},
    ],
    'spec': [
        {'key': 'energy', 'label': 'energy', 'unit': 'keV', 'type': 'float',
         'description': 'Incident beam energy. Values below 1000 are treated as keV, otherwise eV.'},
        {'key': 'mu', 'label': 'mu', 'unit': 'deg', 'type': 'float'},
        {'key': 'eta', 'label': 'eta', 'unit': 'deg', 'type': 'float'},
        {'key': 'phi', 'label': 'phi', 'unit': 'deg', 'type': 'float'},
        {'key': 'nu', 'label': 'nu', 'unit': 'deg', 'type': 'float'},
        {'key': 'delta', 'label': 'delta', 'unit': 'deg', 'type': 'float'},
        {'key': 'detdist', 'label': 'detector distance', 'unit': 'mm',
         'type': 'float',
         'description': 'Sample-to-detector distance.'},
        {'key': 'scanmot', 'label': 'scan motor', 'type': 'choice',
         'choices': ['mu', 'eta', 'phi'],
         'description': 'Motor that defines the scan steps. Pick a listed '
                        'motor or use (custom...) to type a different name.'},
    ],
}

SPEC_DRIVERS = ('h5file',)

def get_config_schema():
    return INSTR_FIELDS