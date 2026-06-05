# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from cohere_beamlines.esrf_id01.diffractometers import Diffractometer
import cohere_beamlines.esrf_id01.detectors as det
from cohere_beamlines.common.instr import Instrument
import os
import h5py


class Instrument_esrf_id01(Instrument):
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
        super(Instrument_esrf_id01, self).__init__(det_obj, diff_obj, conf_params)


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
        params = self.conf_params['config_instr']
        h5_dict = {}

        # Scan numbers start at one but the list is 0 indexed
        h5f = h5py.File(params['h5file'])
        info = h5f[f"{scan}.1"]

        try:
            h5_dict['detector'] = params['detector']
            command = info['title'].asstr()[()].split(" ")
            if command[0] in ("ascan", "a2scan", "a3scan"):
                h5_dict['scanmot'] = command[1]
            else:
                raise IOError(f"{__name__}: Unknown scan type: {command[0]}")
            for mot_mne in self.diff_obj.sampleaxes_mne + self.diff_obj.detectoraxes_mne:
                if mot_mne != h5_dict['scanmot']:
                    h5_dict[mot_mne] = info[f'instrument/positioners/{mot_mne}'][()]
                else:
                    h5_dict['scanmot_posns'] = info[f'instrument/positioners/{mot_mne}'][()]
                    # find the scan motor position at center slice
                    h5_dict[h5_dict['scanmot']] = h5_dict['scanmot_posns'][len(h5_dict['scanmot_posns'])//2]

            h5_dict[self.diff_obj.detectordist_mne] = info[f'instrument/{params["detector"]}/{self.diff_obj.detectordist_name}'][()]

            h5_dict['energy'] = info['instrument/monochromator/Energy'][()]
        except Exception as ex:
            print(f"{__name__}: {ex}")
            raise ex
        h5f.close()

        return h5_dict


    def datainfo4scans(self):
        """
        Finds nodes in hdf5 file that correspond to given scans and scan ranges.
        Parameters
        ----------
        Returns
        -------
        list
        """
        return self.det_obj.nodes4scans(self.scan_ranges)


    def get_scan_array(self, scan_node):
        return self.det_obj.get_scan_array(scan_node)


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
    diff_obj = Diffractometer()
    det_obj = None

    config_params = configs['config_instr']
    h5file = config_params.get('h5file', None)
    if h5file is None:
        msg = 'h5file file must be provided to create Instrument for esrf_id01 beamline'
        raise ValueError(msg)
    # check if the file exist
    if not os.path.isfile(h5file):
        msg = f"h5file {h5file} does not exist"
        raise ValueError(msg)

    detector = config_params.get('detector', None)
    if detector is None:
        msg = 'detector must be provided to create Instrument for esrf_id01 beamline'
        raise ValueError(msg)

    if 'config_prep' in configs:
        config_params.update(configs['config_prep'])
    det_obj = det.create_detector(detector, config_params)

    instr = Instrument_esrf_id01(det_obj, diff_obj, configs)

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
        instr.scan_ranges = scan_ranges

    return instr
