# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import numpy as np
from xrayutilities.io import spec as spec
from cohere_beamlines.beam_diffractometers.common_diff import Diffractometer


class Diffractometer_7iddrobot(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates "7idd" diffractometer with robot detector position.
    """
    name = "7iddrobot"
    sampleaxes = ('x-', 'z-', 'x-', 'y+')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('wedge', 'Chi', 'ThetaN', 'Phi') #wedge is fixed at 10 deg.Maybe put in config if it changed
    sampleaxes_mne = ('wedge','chi','th', 'phi')
    detectoraxes_name = ('Yaw', 'Pitch')
    detectoraxes_mne = ('yaw', 'pitch')
    detectordist_name = 'Radius'
    detectordist_mne = 'radius'

    def __init__(self, params):
        super(Diffractometer_7iddrobot, self).__init__()
        self.specfile = params.get('specfile')


    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """

        params[self.detectordist_mne] = params[self.detectordist_mne] / 1000.0  # convert to meters
        return params


    def parse_metadata(self, scan):
        """
        Reads parameters from spec file for given scan.

        Parameters
        ----------
        scan : int
            scan number to use to recover the saved measurements

        Returns
        -------
        dict with delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector_name, energy
        """
        spec_dict = {}
        if self.specfile is None or scan is None:
            return spec_dict

        # Scan numbers start at one but the list is 0 indexed
        try:
            ss = spec.SPECFile(self.specfile)[scan - 1]
        except Exception as ex:
            print(str(ex))
            print('Could not parse ' + self.specfile)
            return None

        try:
            command = ss.command.split()
            spec_dict['scanmot'] = command[1]
            spec_dict['scanmot_del'] = (float(command[3]) - float(command[2])) / int(command[4])
        except:
            pass

        for mot_mne, mot_name in zip(self.sampleaxes_mne + self.detectoraxes_mne,
                                     self.sampleaxes_name + self.detectoraxes_name):
            try:
                motname = "INIT_MOPO_{m}".format(m=mot_name)
                spec_dict[mot_mne] = ss.init_motor_pos[motname]
            except:
                pass
        try:
            motname = "INIT_MOPO_{m}".format(m=self.detectordist_name)
            spec_dict[self.detectordist_mne] = ss.init_motor_pos[motname]
        except:
            pass

        try:
            spec_dict['energy'] = ss.init_motor_pos['INIT_MOPO_Energy']
        except:
            pass

        try:
            spec_dict['detector'] = str(ss.getheader_element('UIMDET'))
            if spec_dict['detector'].endswith(':'):
                spec_dict['detector'] = spec_dict['detector'][:-1]
        except Exception as ex:
            print(str(ex))

        try:
            roi = ss.getheader_element('UIMR5')
            if type(roi) == list:
                if len(roi) > 0:
                    roi = roi[0]
                    spec_dict['roi'] = [int(n) for n in roi.split()]
        except Exception as ex:
            print(str(ex))

        return spec_dict


def create_diffractometer(diff_name, params):
    if Diffractometer_7iddrobot.name == diff_name:
        return Diffractometer_7iddrobot(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)
