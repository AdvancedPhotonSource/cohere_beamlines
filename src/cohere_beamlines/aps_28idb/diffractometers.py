# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from typing import NamedTuple


class Diffractometer(NamedTuple):
    """
    Encapsulates CHEX diffractometer.
    """
    sampleaxes = ('z-', 'x+', 'y+', 'z-')  # in xrayutilities notation
    detectoraxes = ('z-', 'x+')
    incidentaxis = (0, 1, 0)
    sampleaxes_name = ('Mu', 'Eta', 'Chi', 'Phi')
    sampleaxes_mne = ('mu', 'eta', 'chi', 'phi')
    detectoraxes_name = ('Nu', 'Delta')
    detectoraxes_mne = ('nu', 'del')
    detectordist_name = 'camdist'
    detectordist_mne = 'detdist'
