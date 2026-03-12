# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import numpy as np
import h5py
from cohere_beamlines.common.diff import Diffractometer


class Diffractometer_id01(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates "id01" diffractometer.
    """
    name = "id01"
    sampleaxes = ('y-', 'x-', 'y-')  # in xrayutilities notation
    detectoraxes = ('y-', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('Mu', 'Eta', 'Phi')
    sampleaxes_mne = ('mu', 'eta', 'phi')
    detectoraxes_name = ('Nu', 'Delta')
    detectoraxes_mne = ('nu', 'delta')
    detectordist_name = 'distance'
    detectordist_mne = 'detdist'


    def __init__(self, params):
        super(Diffractometer_id01, self).__init__()
        self.h5 = params.get('h5file', None)
        self.detector = params.get('detector', None)


    def parse_metadata(self, scan):
        """
        Reads parameters from h5 file for given scan.

        Parameters
        ----------
        h5file : str
            h5 file name

        scan : int
            scan number to use to recover the saved measurements

        diff : object
            diffractometer object

        Returns
        -------
        dict with delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector_name, energy
        """
        h5_dict = {}

        # Scan numbers start at one but the list is 0 indexed
        h5f = h5py.File(self.h5)
        info = h5f[f"{scan}.1"]

        try:
            h5_dict['detector'] = self.detector
            command = info['title'].asstr()[()].split(" ")
            if command[0] in ("ascan", "a2scan", "a3scan"):
                h5_dict['scanmot'] = command[1]
                h5_dict['scanmot_del'] = (float(command[3]) - float(command[2])) / int(command[4])
            else:
                raise IOError(f"{__name__}: Unknown scan type: {command[0]}")
            for mot_mne in self.sampleaxes_mne + self.detectoraxes_mne:
                if mot_mne != h5_dict['scanmot']:
                    h5_dict[mot_mne] = info[f'instrument/positioners/{mot_mne}'][()]
                else:
                    h5_dict[mot_mne] = info[f'instrument/positioners/{mot_mne}'][()][0]

            h5_dict[self.detectordist_mne] = info[f'instrument/{self.detector}/{self.detectordist_name}'][()]

            h5_dict['energy'] = info['instrument/monochromator/Energy'][()]
        except Exception as ex:
            print(f"{__name__}: {ex}")
            raise ex
        h5f.close()

        return h5_dict


def create_diffractometer(diff_name, params):
    if Diffractometer_id01.name == diff_name:
        return Diffractometer_id01(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)
