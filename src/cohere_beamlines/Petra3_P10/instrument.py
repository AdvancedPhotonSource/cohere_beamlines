# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
from cohere_beamlines.Petra3_P10.diffractometers import Diffractometer
import cohere_beamlines.Petra3_P10.detectors as det
import cohere_beamlines.Petra3_P10.p10_scan_reader as p10sr
from cohere_beamlines.common.instr import Instrument
import cohere_core.utilities as ut


class Instrument_Petra3_P10(Instrument):
    """
      This class encapsulates istruments: diffractometer and detector used for that experiment.
      It provides interface to get the classes encapsulating the diffractometer and detector.
    """
    def __init__(self, det_obj, diff_obj, conf_params):
        """
        Constructor

        :param det_obj: detector object, can be None
        :param diff_obj: diffractometer object, can be None
        """
        super(Instrument_Petra3_P10, self).__init__(det_obj, diff_obj, conf_params)


    def convert_units(self, params):
        """
        Converts detectordist value from mm to m.
        :return:
        """

        params[self.diff_obj.detectordist_mne] = params[self.diff_obj.detectordist_mne] / 1000.0  # convert to meters
        return params


    #Here the fiofile is the P10 fio object.  So no need to read a file.
    def parse_metadata(self, scan, **kwargs):
        """
        Reads parameters from fio file for given scan. The fio file is derived from data_dir sample and scan.
        :param data_dir: directory where data along with fio file are saved
        :param sample: sample name that is used as subdirectory where the fio file is saved
        :param scan: scan defines the subdirectory
        :return: dict with optional params: scanmot, scanmot_del, detdist, detector, energy
        """
        if 'data_dir' in kwargs:
            data_dir = kwargs.get('data_dir', None)
            sample = kwargs.get('sample', None)
        else:
            params = self.conf_params['config_instr']
            data_dir = params.get('data_dir', None)
            sample = params.get('sample', None)
        if data_dir is None or sample is None:
            return {}
        if not os.path.isdir(data_dir):
            print (f"the data path {data_dir} does not exist, parsing not possible." )
            return {}
        if not os.path.isdir(ut.join(data_dir, sample + '_{:05d}'.format(scan))):
            print (f"the data/sample path {data_dir}/{sample + '_{:05d}'.format(scan)} does not exist, parsing not possible." )
            return {}
        fio_dict = {}
        scanmeta = p10sr.P10Scan(data_dir, sample, scan, pathsave='', creat_save_folder=False)

        scanmot = scanmeta.get_scan_motor()
        fio_dict['scanmot'] = scanmot
        fio_dict['scanmot_posns'] = scanmeta.get_scan_data(scanmot)
        fio_dict['scan_step'] = (fio_dict['scanmot_posns'][-1] - fio_dict['scanmot_posns'][0]) / len(fio_dict['scanmot_posns'])

        for mot_mne, mot_name in zip(self.diff_obj.sampleaxes_mne + self.diff_obj.detectoraxes_mne,
                                     self.diff_obj.sampleaxes_name + self.diff_obj.detectoraxes_name):
            fio_dict[mot_mne] = scanmeta.get_motor_pos(mot_mne)

        fio_dict[self.diff_obj.detectordist_mne] = scanmeta.get_motor_pos(self.diff_obj.detectordist_name)

        fio_dict['energy'] = scanmeta.get_motor_pos('fmbenergy')

        try:
            fio_dict['detector'] = scanmeta.get_motor_pos('_ccd')
        except Exception as ex:
            print(str(ex))

        return fio_dict


    def datainfo4scans(self):
        """
        Finds existing sub-directories in data_dir that correspond to given scans and scan ranges.
        Parameters
        ----------
        Returns
        -------
        list
        """
        return self.det_obj.dirs4scans(self.scan_ranges)


    def get_scan_array(self, scan_dir):
        return self.det_obj.get_scan_array(scan_dir)


def create_instr(configs, **kwargs):
    """
    Build factory for the Instrument class.

    Parameters
    ----------
    configs : dict of dicts
        the parameters parsed from config files

    Returns
    -------
    (str, Object)
        error msg, Instrument object or None
    """
    det_obj = None
    diff_obj = Diffractometer()
    scan_ranges = None
    # set parameters from config_instr
    config_params = configs['config_instr']

    scan = configs['config'].get('scan', None)
    if scan is not None:
        # 'scan' is configured as string. It can be a single scan, range, or combination separated by comma.
        # Parse the scan into list of scan ranges, defined by starting scan, and ending scan, inclusive.
        # The single scan has range defined as the same starting and ending scan.
        scan_ranges = []
        scan_units = [u for u in scan.replace(' ','').split(',')]
        for u in scan_units:
            if '-' in u:
                r = u.split('-')
                scan_ranges.append([int(r[0]), int(r[1])])
            else:
                scan_ranges.append([int(u), int(u)])

    det_name = config_params.get('detector', None)
    if det_name is None and scan is not None:
        # try to parse detector name
        # Find the first scan to parse detector params.
        first_scan = scan_ranges[0][0]
        # the directories for Petra are structured as follows: <data_dir>/<sample>scan
        # check here if that directory exist
        data_dir = config_params['data_dir']
        scan_subdir = config_params['sample'] + '_{:05d}'.format(int(scan))
        if not os.path.isdir(ut.join(data_dir, scan_subdir)):
            msg = "cannot parse det_name, the data/sample path does not exist"
            raise ValueError(msg)

        scanmeta = p10sr.P10Scan(config_params.get('data_dir'), config_params.get('sample'), first_scan, pathsave='', creat_save_folder=True)
        det_name = scanmeta.get_motor_pos('_ccd')

    if det_name is None:
        msg = 'detector name not configured and could not be parsed'
        raise ValueError(msg)

    # add parameters from the config_prep
    if 'config_prep' in configs:
        config_params.update(configs['config_prep'])

    need_det = kwargs.get('need_det', False)
    if need_det:
        # check only if detector is created for reading data
        # check for parameters, it will raise exception if failed
        det.check_mandatory_params(det_name, config_params)

    det_obj = det.create_detector(det_name, config_params)

    instr = Instrument_Petra3_P10(det_obj, diff_obj, configs)
    instr.scan_ranges = scan_ranges

    return instr
