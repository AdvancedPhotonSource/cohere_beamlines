# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
import os
import h5py
from cohere_beamlines.aps_20ide.diffractometers import Diffractometer
import cohere_beamlines.aps_20ide.detectors as det
from cohere_beamlines.common.instr import Instrument
import cohere_core.utilities as ut


class Instrument_aps_20ide(Instrument):
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
        super(Instrument_aps_20ide, self).__init__(det_obj, diff_obj, conf_params)


    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """

        for ax in self.diff_obj.detectoraxes_mne:
            params[ax] = params[ax] / 1000
        return params


    def parse_metadata(self, scan, **kwargs):
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
        dict with VFF_ETA, VFF_R, scanmot, DetZ, detector_name, energy
        """
        h5_dict = {}
        if 'data_dir' in kwargs:
            data_dir = kwargs['data_dir']
        else:
            params = self.conf_params['config_instr']
            data_dir = params.get('data_dir', None)
        if data_dir is None:
            return h5_dict

        # find the file by scan number
        for scanfile in sorted(os.listdir(data_dir)):
            scanfile_full_path = ut.join(data_dir, scanfile)
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
        scanmot = self.diff_obj.sampleaxes_mne[0]
        h5_dict['scanmot'] = scanmot
        try:
            h5_dict['scanmot_posns'] = h5f[f'SMS/E/HR/{scanmot}'][:]
        except:
            pass
        h5_dict['scan_step'] = (h5_dict['scanmot_posns'][-1] - h5_dict['scanmot_posns'][0]) / len(h5_dict['scanmot_posns'] -1)
        for mot_mne in self.diff_obj.detectoraxes_mne:
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


    def datainfo4scans(self):
        """
        Finds existing sub-directories in data_dir that correspond to given scans and scan ranges.
        Parameters
        ----------
        Returns
        -------
        list
        """
        return self.det_obj.files4scans(self.scan_ranges)


    def get_scan_array(self, scan_dir):
        return self.det_obj.get_scan_array(scan_dir)


def create_instr(configs, **kwargs):
    """
    Build factory for the Instrument class.

    Parameters
    ----------
    configs : dict
        the parameters parsed from config file

    Returns
    -------
    (str, Object)
        error msg, Instrument object or None
    """
    det_obj = None
    diff_obj = Diffractometer()
    main_config_params = configs['config']

    det_name = configs['config_instr'].get('detector', None)
    if det_name is None:
        raise ValueError('detector name not configured and could not be parsed')

    # set detector parameters to configured parameters in config_instr and processing
    # parameters from config_prep
    det_params = configs['config_instr']
    if 'config_prep' in  configs:
        det_params.update(configs['config_prep'])

    need_det = kwargs.get('need_det', False)
    if need_det:
        # check only if detector is created for reading data
        # check for parameters, it will raise exception if failed
        det.check_mandatory_params(det_name, det_params)

    det_obj = det.create_detector(det_name, det_params)

    instr = Instrument_aps_20ide(det_obj, diff_obj, configs)
    # set scan ranges in instrument class
    scan_ranges = None
    scan = main_config_params.get('scan', None)
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
    instr.scan_ranges = scan_ranges

    return instr