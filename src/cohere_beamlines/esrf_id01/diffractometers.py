# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
from typing import NamedTuple


class Diffractometer(NamedTuple):
    """
    Encapsulates "id01" diffractometer.
    """
    sampleaxes = ('y-', 'x-', 'y-')  # in xrayutilities notation
    detectoraxes = ('y-', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('Mu', 'Eta', 'Phi')
    sampleaxes_mne = ('mu', 'eta', 'phi')
    detectoraxes_name = ('Nu', 'Delta')
    detectoraxes_mne = ('nu', 'delta')
    detectordist_name = 'distance'
    detectordist_mne = 'detdist'
