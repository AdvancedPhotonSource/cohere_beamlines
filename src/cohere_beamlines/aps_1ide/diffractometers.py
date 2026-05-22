# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import numpy as np
from xrayutilities.io import spec as spec
from cohere_beamlines.common.diff import Diffractometer


class Diffractometer_1ide(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates "1ide" diffractometer.
    """
    name = "1ide"
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

    def __init__(self, params):
        super(Diffractometer_1ide, self).__init__(params)
        self.specfile = params.get('specfile', None)


    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """

        params[self.detectordist_mne] = params[self.detectordist_mne] / 1000.0  # convert to meters
        params['vff_r'] = params['vff_r'] / 1000 + params['vff_r_offset']
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
        dict with metadata
        """
        spec_dict = {}

        # Scan numbers start at one but the list is 0 indexed
        try:
            sf = spec.SPECFile(self.specfile)
            ss = sf[scan - 1]
        except Exception as ex:
            print(str(ex))
            print('Could not parse ' + self.specfile)
            return None

        try:
            command = ss.command.split()
            spec_dict['scanmot'] = command[1]
        except:
            pass

        motmne_name_dict = {**dict(zip(self.sampleaxes_mne, self.sampleaxes_name)),
                            **dict(zip(self.detectoraxes_mne, self.detectoraxes_name))}

        for mot_mne, mot_name in motmne_name_dict.items():
            try:
                motname = "INIT_MOPO_{m}".format(m=mot_name)
                spec_dict[mot_mne] = ss.init_motor_pos[motname]
            except:
                print("failed from spec", mot_mne, mot_name)

        try:
            motname = "INIT_MOPO_{m}".format(m=self.detectordist_name)
            spec_dict['detdist'] = ss.init_motor_pos[motname]
        except:
            pass

        try:
            spec_dict['scanmot_posns'] = spec.getspec_scan(sf, scan, motmne_name_dict[spec_dict['scanmot']])[0]
        except Exception as ex:
            print(str(ex))

        try:
            spec_dict['detector'] = str(ss.getheader_element('UIMDET'))
            if spec_dict['detector'].endswith(':'):
                spec_dict['detector'] = spec_dict['detector'][:-1]
        except Exception as ex:
            print(str(ex))

        return spec_dict


def create_diffractometer(diff_name, params):
    if Diffractometer_1ide.name == diff_name:
        return Diffractometer_1ide(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)
