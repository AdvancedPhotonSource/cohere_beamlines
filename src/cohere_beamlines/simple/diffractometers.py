# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from typing import NamedTuple


class Diffractometer(NamedTuple):
    """
    Encapsulates "34idc" diffractometer.
    """
    sampleaxes = ('y+', 'z-', 'y+')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('Theta', 'Chi', 'Phi')
    sampleaxes_mne = ('th', 'chi', 'phi')
    detectoraxes_name = ('Delta', 'Gamma')
    detectoraxes_mne = ('delta', 'gamma')
    detectordist_name = 'camdist'
    detectordist_mne = 'detdist'

