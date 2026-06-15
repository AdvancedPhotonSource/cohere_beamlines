"""`simple` InstrTab schema. See aps_34idc/instr_schema.py for the format reference.

Minimal stub beamline: parse_metadata returns {}, so the spec section
stays empty and the user fills the general fields by hand.
"""

INSTR_FIELDS = {
    'general': [
        {
            'key': 'data_dir', 'label': 'data directory', 'type': 'dir',
            'description': 'Directory containing the raw detector frames.',
        },
    ],
    'spec': [],
}

SPEC_DRIVERS = ()
