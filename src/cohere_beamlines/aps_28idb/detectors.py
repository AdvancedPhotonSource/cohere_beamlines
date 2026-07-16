# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
import hdf5plugin
import numpy as np
import os
import cohere_core.utilities as ut
from cohere_beamlines.common.det import Detector
from abc import abstractmethod
import h5py


class aps28Detector(Detector):
    """
    Abstract class representing detector.
    """

    def __init__(self, params):
        super(aps28Detector, self).__init__(params)

    def files4scans(self, scans):
        """
        Finds data files that correspond to given scans or scan ranges.

        :param scans : list
            list of sub-lists defining scan ranges, ordered. For single scan a range has the same scan as beginning and end.
            one scan example:
            scans : [[2834, 2834]]
            returns : [[(2834, f'{path}/data_S2834)]]

            separate ranges example:
            scans: [[2825, 2831], [2834, 2834], [2840, 2846]]
            returns: [[(2825, f'{path}/data_S2825'), (2828, f'{path}/data_S2828'), (2831, f'{path}/data_S2831')],
             [(2834, f'{path}/data_S2834)],
             [(2840, f'{path}/data_S2840'), (2843, f'{path}/data_S2843'), (2846, f'{path}/data_S2846')]]

        :return:
        list of sub-lists, each sublist containing tuples with the input scans and corresponding data directories
         within scan ranges.
        """
        # create empty results list that allocates a sub-list for each scan range
        first_scan = scans[0][0]
        last_scan = scans[-1][-1]
        scans_files = {}
        for scanfile in sorted(os.listdir(self.data_dir)):
            scanfile_full = ut.join(self.data_dir, scanfile)
            if not os.path.isfile(scanfile_full) or not scanfile_full.endswith('.h5'):
                continue
            try:
                # # first chop off the "_00000.h5" and get the scan number
                # scan = scanfile[:-8]
                # scan = int(scanfile[:-3].split('_')[-1])
                scan = int(scanfile.split('.')[0].split('_')[-2][1:])
            except:
                continue
            if scan < first_scan:
                continue
            elif scan > last_scan:
                break
            scans_files[scan] = scanfile_full
            if scan == last_scan:
                break

        # remove excluded scans
        scans_files = {key: value for key, value in scans_files.items() if key not in self.exclude_scans}

        # remove scans that have less frames than configured.
        if self.min_frames > 0:
            short_in_frames = []
            for (scan, fn) in scans_files.items():
                # open file, check number of
                with h5py.File(fn, "r") as h5f:
                    if h5f['entry/data/data'].shape[0] < self.min_frames:
                        print(f'data for scan {scan} contains fewer than {self.min_frames} frames.')
                        short_in_frames.append(scan)
            if len(short_in_frames) > 0:
                scans_files = {key: value for key, value in scans_files.items() if key not in short_in_frames}

        # distribute by ranges
        scans_dirs_ranges = [[(k, v) for k, v in scans_files.items() if k >= scans[i][0] and k <= scans[i][-1]] for i in
                             range(len(scans))]

        # remove empty sub-lists
        scans_dirs_ranges = [e for e in scans_dirs_ranges if len(e) > 0]
        return scans_dirs_ranges


    def get_scan_array(self, scan_info):
        """
        Reads/loads raw data file and applies correction.

        Reads raw data from a h5 file. The file name is in scan scan_info.

        :param scan_info: h5 file that contains raw data
        :return: corrected data array
        """
        h5file = scan_info
        with h5py.File(h5file, "r") as h5f:
            data = h5f['entry/data/data'][:].T

        offset = [0, 0]

        if self.roi is not None:
            data, offset = self.get_roi_slice(data)
        data = self.correct(data)

        if self.max_crop is not None:
            data, offset = self.get_max_crop_slice(data, offset)

        return data, offset


    @abstractmethod
    def check_mandatory_params(self, params):
        """
        checks if all mandatory parameters are in params.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """

    @abstractmethod
    def correct(self, data):
        """
        Applies the correction for detector.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """


class Detector_s28eiger2_si(aps28Detector):
    """
    Subclass of Detector. Encapsulates "s28eiger2-si" detector.
    """
    name = "s28eiger2-si"
    dims = (1028, 512)
    pixel = (75.0e-6, 75e-6)
    pixelorientation = ('x-', 'z-')  # in xrayutilities notation
    darkfield = None
    data_dir = None
    Imult = 1.0
    beam_zero = [440, 292]  # used for RSM calculation.


    def __init__(self, params):
        super(Detector_s28eiger2_si, self).__init__(params)
        # The detector attributes for background/whitefield/etc need to be set to read frames
        # this will capture things like data directory, darkfield_filename, etc.
        self.data_dir = params.get('data_dir', None)
        # the det_roi is detector roi selecting area that was captured, typically parsed from spec file.
        # It is specific to 34idc.
        if 'det_roi' in params:
            self.det_roi = params.get('det_roi')
        if 'darkfield_filename' in params:
            self.darkfield = ut.read_tif(params.get('darkfield_filename'))
        if 'whitefield_filename' in params:
            self.whitefield = ut.read_tif(params.get('whitefield_filename'))

    # TIM1 only needs bad pixels deleted.  Even that is optional.
    def correct(self, data):
        """
        Gets raw data from a file, and applies correction for s28eiger2_si detector, i.e. darkfield.
        Parameters
        ----------
        data : ndarray
            data array
        Returns
        -------
        frame : ndarray
            frame after correction
        """
        if self.darkfield is not None:
            if len(self.darkfield.shape) == 2:
                cor = self.darkfield[:, :, np.newaxis]
            else:
                cor = self.darkfield
            data = data * cor

        if self.whitefield is not None:
            if len(self.whitefield.shape) == 2:
                cor = self.whitefield[:, :, np.newaxis]
            else:
                cor = self.whitefield
            data = data / cor * self.Imult
        else:
            pass

        data = np.nan_to_num(data)

        return data

    def get_det_roi(self):
        return self.det_roi[:4]


    @staticmethod
    def check_mandatory_params(params):
        """
        For the 34idcTIM1 detector the data directory is mandatory. The darkfield file is optional.

        :return: message indicating problem or empty message if all is ok
        """
        if 'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for 34idcTIM1 detector.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory{data_dir} does not exist.'
            raise ValueError(msg)


    @staticmethod
    def check_mandatory_params(params):
        """
        For the 34idcTIM2 detector the data directory, whitefiled_filename, darkfield_ilename
        are mandatory parameters.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """
        if 'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for 34idcTIM2 detector.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory{data_dir} does not exist.'
            raise ValueError(msg)

        # if 'whitefield_filename' not in params:
        #     msg = 'whitefield_filename parameter not configured, mandatory for 34idcTIM2 detector.'
        #     raise ValueError(msg)
        # whitefield = params['whitefield_filename']
        # if not os.path.isfile(whitefield):
        #     msg = f'whitefield_filename file {whitefield} does not exist.'
        #     raise ValueError(msg)
        #
        # if 'darkfield_filename' not in params:
        #     msg = 'darkfield_filename parameter not configured, mandatory for 34idcTIM2 detector.'
        #     raise ValueError(msg)
        # darkfield = params['darkfield_filename']
        # if not os.path.isfile(darkfield):
        #     msg = f'darkfield_filename file {darkfield} does not exist.'
        #     raise ValueError(msg)


dets = {detector.name: detector for detector in aps28Detector.__subclasses__()}


def create_detector(det_name, params):
    return dets[det_name](params)


def check_mandatory_params(det_name, params):
    return dets[det_name].check_mandatory_params(params)
