import numpy as np
from cohere_beamlines.common.diff import Diffractometer


class Diffractometer_simple(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates any diffractometer. Based on aps_34idc beamline.
    """
    name = "simple"
    sampleaxes = ('y+', 'z-', 'y+')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('Theta', 'Chi', 'Phi')
    sampleaxes_mne = ('th', 'chi', 'phi')
    detectoraxes_name = ('Delta', 'Gamma')
    detectoraxes_mne = ('delta', 'gamma')
    detectordist_name = 'camdist'
    detectordist_mne = 'detdist'


    def __init__(self, params):
        super(Diffractometer_simple, self).__init__()
        self.data_dir = params['data_dir']


    def convert_units(self, params):
        """
        Converts detectordist value from mm to m.
        :return:
        """
        params[self.detectordist_mne] = params[self.detectordist_mne] / 1000.0  # convert to meters
        return params


    def parse_metadata(self, scan):
        return {}


def create_diffractometer(diff_name, params):
    if Diffractometer_simple.name == diff_name:
        return Diffractometer_simple(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)
