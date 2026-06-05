# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
from typing import NamedTuple

class Diffractometer(NamedTuple):
    """
    Encapsulates "7idd" diffractometer with robot detector position.
    """
    sampleaxes = ('x-', 'z-', 'x-', 'y+')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('wedge', 'Chi', 'ThetaN', 'Phi') #wedge is fixed at 10 deg.Maybe put in config if it changed
    sampleaxes_mne = ('wedge','chi','th', 'phi')
    detectoraxes_name = ('Yaw', 'Pitch')
    detectoraxes_mne = ('yaw', 'pitch')
    detectordist_name = 'Radius'
    detectordist_mne = 'radius'
