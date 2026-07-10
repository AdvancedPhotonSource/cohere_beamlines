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
    detectoraxes = ('z+', 'x+')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('Mu', 'Eta', 'Chi', 'Phi')
    sampleaxes_mne = ('Mu', 'Eta', 'Chi', 'Phi')
    detectoraxes_name = ('Nu', 'Delta')
    detectoraxes_mne = ('Nu', 'delta')
    # detectordist_name = 'camdist'
    # detectordist_mne = 'detdist'
