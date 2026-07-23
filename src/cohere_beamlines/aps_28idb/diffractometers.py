# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from typing import NamedTuple


class Huber(NamedTuple):
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


class Tower(NamedTuple):
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


def create_diffractometer(diff_name):
    if diff_name == 'tower':
        return Tower()
    elif diff_name == 'huber':
        return Huber()
    else:
        raise ValueError('diffractometer name not defined')