"""InstrTab schema. The other beamlines' instr_schema.py files
follow the same shape; refer here for the full reference.

The Jupyter GUI's InstrTab reads this module to render the per-beamline
instrument form. Two top-level objects must be exported:

  INSTR_FIELDS = {
      'general': [<field>, ...],   # user-managed; never overwritten by spec parse
      'spec':    [<field>, ...],   # auto-populated by the Instrument's parse_metadata
  }
  SPEC_DRIVERS = (<key>, ...)       # general-section keys whose change re-parses spec

Each <field> is a dict; the recognised keys are:

  key          (str, required)  the config_<name> key written to conf/config_instr.
                                 MUST match what the beamline Instrument reads from
                                 config_instr OR what parse_metadata() emits.
  label        (str, required)  human-readable label shown in the form
  type         (str)            one of 'text' (default) | 'bool' | 'choice' |
                                 'dir' | 'file' | 'float' | 'int'
  unit         (str)            optional unit shown in small grey after the label
                                 (e.g. 'keV', 'deg', 'mm')
  description  (str)            hover-tooltip text on the label
  placeholder  (str)            placeholder for text/float/int inputs
  choices      (list)           options for type='choice'. Each entry is either
                                 a string (display == saved key) OR a
                                 (display, key) tuple (the user picks 'display'
                                 and the GUI saves 'key'). For scan motors the
                                 saved key MUST match what parse_metadata()
                                 puts into spec_dict['scanmot'].
  auto_choices (str)            'detector' -- introspect the beamline's
                                 detectors.py for class .name attributes. Use
                                 this when the set of valid choices lives in
                                 code; declare 'choices' explicitly when it
                                 doesn't. (Note: 'diffractometer' is no longer a
                                 valid auto_choices source -- the diffractometer
                                 is now a bare NamedTuple hardcoded per beamline,
                                 with no .name; it resolves to an empty list.)

SPEC_DRIVERS lists the general-section keys whose value drives spec parsing
(typically the spec/h5 file path, e.g. 'specfile' / 'h5file' / 'data_dir').
When any driver field changes, the GUI re-invokes parse_metadata and refreshes
every spec field with the returned values.

When adding/renaming a field, verify the key matches diffractometers.py /
detectors.py exactly. Mismatches don't error, the GUI just silently drops
the value at save time or never populates the widget.
"""

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
            'key': 'det_roi', 'label': 'detector ROI',
            'placeholder': 'e.g., [0, 256, 0, 256]',
            'description': 'Detector ROI [y0, height, x0, width].',
        },
    ],
    'spec': [
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
    ],
}

SPEC_DRIVERS = ('specfile',)
