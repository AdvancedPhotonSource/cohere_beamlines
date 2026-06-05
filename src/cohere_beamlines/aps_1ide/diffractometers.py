# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
from typing import NamedTuple


class Diffractometer(NamedTuple):
    """
    Encapsulates "1ide" diffractometer.
    """
    sampleaxes=('y-')  #omega is postive down
    detectoraxes=('z+','ty','tx')
    incidentaxis = (0, 0, 1)
    #motors from spec file.
    sampleaxes_name = ('AeroTech',)
    sampleaxes_mne = ('aero',)
    detectoraxes_name = ('vff_eta', 'vff_r', 'vff_eta_offset')
    detectoraxes_mne = ('vff_eta', 'vff_r', 'vff_eta_offset')
    detectordist_name = 'detdist'
    detectordist_mne = 'detdist'
    #det dist will be in the config file.  Combination of dist to eta and x95 offset to back.
