# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from typing import NamedTuple

class Diffractometer(NamedTuple):
    """
    Encapsulates "P10sixc" diffractometer.
    """
    sampleaxes = ('y+', 'x-', 'z+', 'y-')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('mu', 'om', 'chi', 'phi')
    sampleaxes_mne = ('mu', 'om', 'chi', 'phi')
    detectoraxes_name = ('Gamma', 'Delta')
    detectoraxes_mne = ('gam','del')
    detectordist_name = '_distance'
    detectordist_mne = 'detdist'
