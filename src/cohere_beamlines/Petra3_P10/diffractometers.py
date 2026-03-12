# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os.path
import cohere_core.utilities as ut
import numpy as np
from cohere_beamlines.common.diff import Diffractometer
import cohere_beamlines.Petra3_P10.p10_scan_reader as p10sr


class Diffractometer_P10sixc(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates "P10sixc" diffractometer.
    """
    name = "P10sixc"
    sampleaxes = ('y+', 'x-', 'z+', 'y-')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('mu', 'om', 'chi', 'phi')
    sampleaxes_mne = ('mu', 'om', 'chi', 'phi')
    detectoraxes_name = ('Gamma', 'Delta')
    detectoraxes_mne = ('gam','del')
    detectordist_name = '_distance'
    detectordist_mne = 'detdist'

    def __init__(self, params):
        super(Diffractometer_P10sixc, self).__init__()
        self.data_dir = params['data_dir']
        self.sample = params['sample']


    def convert_units(self, params):
        """
        Converts detectordist value from mm to m.
        :return:
        """

        params[self.detectordist_mne] = params[self.detectordist_mne] / 1000.0  # convert to meters
        return params


    #Here the fiofile is the P10 fio object.  So no need to read a file.
    def parse_metadata(self, scan):
        """
        Reads parameters from fio file for given scan. The fio file is derived from data_dir sample and scan.
        :param data_dir: directory where data along with fio file are saved
        :param sample: sample name that is used as subdirectory where the fio file is saved
        :param scan: scan defines the subdirectory
        :return: dict with optional params: scanmot, scanmot_del, detdist, detector, energy
        """
        # check if the values are meaningful
        if self.data_dir is None or self.sample is None:
            return {}
        if not os.path.isdir(self.data_dir):
            print (f"the data path {self.data_dir} does not exist, parsing not possible." )
            return {}
        if not os.path.isdir(ut.join(self.data_dir, self.sample + '_{:05d}'.format(scan))):
            print (f"the data/sample path {self.data_dir}/{self.sample + '_{:05d}'.format(scan)} does not exist, parsing not possible." )
            return {}
        fio_dict = {}
        scanmeta = p10sr.P10Scan(self.data_dir, self.sample, scan, pathsave='', creat_save_folder=False)
        command = scanmeta.command.split()
        fio_dict['scanmot'] = command[1]
        fio_dict['scanmot_del'] = (float(command[3]) - float(command[2])) / int(command[4])

        for mot_mne, mot_name in zip(self.sampleaxes_mne + self.detectoraxes_mne,
                                     self.sampleaxes_name + self.detectoraxes_name):
            fio_dict[mot_mne] = scanmeta.get_motor_pos(mot_mne)

        fio_dict[self.detectordist_mne] = scanmeta.get_motor_pos(self.detectordist_name)


        fio_dict['energy'] = scanmeta.get_motor_pos('fmbenergy')

        try:
            fio_dict['detector'] = scanmeta.get_motor_pos('_ccd')
        except Exception as ex:
            print(str(ex))

        return fio_dict


    @staticmethod
    def check_mandatory_params(params):
        """
        For the P10sixc diffractometer the data_dir, sample are mandatory parameters.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """
        if  'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for P10sixc diffractometer.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory {data_dir} does not exist.'
            raise ValueError(msg)

        if 'sample' not in params:
            msg = 'sample parameter not configured, mandatory for e4m detector.'
            raise ValueError(msg)


def create_diffractometer(diff_name, params):
    if Diffractometer_P10sixc.name == diff_name:
        return Diffractometer_P10sixc(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)


def check_mandatory_params(diff_name, params):
    if Diffractometer_P10sixc.name == diff_name:
        return Diffractometer_P10sixc.check_mandatory_params(params)
    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)
