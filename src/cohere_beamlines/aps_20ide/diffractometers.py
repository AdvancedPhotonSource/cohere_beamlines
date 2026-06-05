# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
from typing import NamedTuple

class Diffractometer(NamedTuple):
    """
    Subclass of Diffractometer. Encapsulates "20ide" diffractometer.
    """
    sampleaxes=('y+')  #omega is postive up
    detectoraxes=('tz','tx','ty')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('LabMotion',)
    sampleaxes_mne = ('samRy',)
    detectoraxes_name = ('DetZ', 'DetX', 'DetY')
    detectoraxes_mne = ('DetZ', 'DetX', 'DetY')
    detectordist_name = 'DetZ'
    detectordist_mne = 'DetZ'
