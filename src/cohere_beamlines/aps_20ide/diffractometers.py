# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
import os
import numpy as np
import h5py
import numpy as np
from cohere_beamlines.common.diff import Diffractometer
import cohere_core.utilities as ut


class Diffractometer_20ide(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates "20ide" diffractometer.
    """
    name = "20ide"
    sampleaxes=('y+')  #omega is postive up
    detectoraxes=('tz','tx','ty')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('LabMotion',)
    sampleaxes_mne = ('samRy',)
    detectoraxes_name = ('DetZ', 'DetX', 'DetY')
    detectoraxes_mne = ('DetZ', 'DetX', 'DetY')
    detectordist_name = 'DetZ'
    detectordist_mne = 'DetZ'


    def __init__(self, params):
        super(Diffractometer_20ide, self).__init__(params)
        self.data_dir = params.get('data_dir', None)


    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """

        for ax in self.detectoraxes_mne:
            params[ax] = params[ax] / 1000
        return params


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
        dict with VFF_ETA, VFF_R, scanmot, scanmot_del, DetZ, detector_name, energy
        """
        h5_dict = {}

        # find the file by scan number
        for scanfile in sorted(os.listdir(self.data_dir)):
            scanfile_full_path = ut.join(self.data_dir, scanfile)
            if not os.path.isfile(scanfile_full_path) or not scanfile_full_path.endswith('.h5'):
                continue
            # chop off the ".h5" and get the scan number
            try:
                # read_scan = int(scanfile[:-3].split('_')[-1])
                # The format is xxx_ddd.detectorname.h5
                read_scan = int(scanfile.split('.')[0].split('_')[-1])
            except:
                continue
            if read_scan == scan:
                h5file = scanfile_full_path
                break

        h5f = h5py.File(h5file)
        scanmot = self.sampleaxes_mne[0]
        h5_dict['scanmot'] = scanmot
        try:
            h5_dict['scanmot_posns'] = h5f[f'SMS/E/HR/{scanmot}'][:]
        except:
            pass
        for mot_mne in self.detectoraxes_mne:
            try:
                h5_dict[mot_mne] = h5f[f'DMS/{mot_mne}'][0]
            except:
                pass
        # detectordist_mne is the same as detectoraxes_mne[0]
        # try:
        #     h5_dict[self.detectordist_mne] = h5f[f'DMS/{self.detectordist_name}'][0]
        # except:
        #     pass
        try:
            h5_dict['energy'] = h5f['HEM/Energy'][0]
        except Exception as ex:
            # print(f"{__name__}: {ex}")
            pass

        h5f.close()
        return h5_dict


def create_diffractometer(diff_name, params):
    if Diffractometer_20ide.name == diff_name:
        return Diffractometer_20ide(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)