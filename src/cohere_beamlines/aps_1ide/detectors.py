# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
import numpy as np
import cohere_core.utilities as ut
from cohere_beamlines.common.det import Detector
from abc import abstractmethod
import re


class aps1Detector(Detector):
    """
    Class representing detector.

    Some functions are common for all detectors and are implemented in the base class.
    """

    def __init__(self, params):
        super(aps1Detector, self).__init__(params)

    def dirs4scans(self, scans):
        """
        Finds directories with data that correspond to given scans or scan ranges.

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
        scans_dirs_ranges = [[] for _ in range(len(scans))]
        sr_idx = 0
        scan_range = scans[sr_idx]
        scans_dirs = scans_dirs_ranges[sr_idx]
        
        #for scandir in sorted(glob.glob(os.path.join(self.data_dir, self.sample+'*'))):
        # check for directories
        for scandir in sorted(os.listdir(self.data_dir)):
            scandir_full = ut.join(self.data_dir, scandir)
            if os.path.isdir(scandir_full):
                # test the directory name if it ends with patten "_Sdddd", where d is a digit
                scan_dir_pattern = r'_S[0-9]{4}$'
                dir_end = re.search(scan_dir_pattern, scandir)
                if dir_end is not None:
                    dir_end = dir_end.group()
                    # find last digits, which is scan
                    last_digits = dir_end[-4:]
                    scan = int(last_digits)
                else:
                    continue
                if scan < scan_range[0]:
                    continue
                elif scan <= scan_range[-1]:
                    # scan within range
                    # before adding scan check if there is enough data files
                    if len(os.listdir(scandir_full)) >= self.min_frames and scan not in self.exclude_scans:
                        scans_dirs.append((scan, scandir_full))
                    if scan == scan_range[-1]:
                        sr_idx += 1
                        if sr_idx > len(scans) - 1:
                            break
                        scan_range = scans[sr_idx]
                        scans_dirs = scans_dirs_ranges[sr_idx]
                elif scan > scan_range[-1]:
                    sr_idx += 1
                    if sr_idx > len(scans) - 1:
                        break
                    scan_range = scans[sr_idx]
                    scans_dirs = scans_dirs_ranges[sr_idx]
                    if (scan >= scan_range[0] and scan <= scan_range[-1]
                            and len(os.listdir(scandir_full)) >= self.min_frames) and scan not in self.exclude_scans:
                            scans_dirs.append((scan, scandir_full))

        # remove empty sub-lists
        scans_dirs_ranges = [e for e in scans_dirs_ranges if len(e) > 0]
        return scans_dirs_ranges


    def get_scan_array(self, scan_info):
        """
        Reads/loads raw data file and applies correction. The correction is detector dependent.

        Reads raw data from a directory. The directory name is scan_info. The raw data is in form of 2D
        frames. The frames are read, corrected and stocked into 3D data
        This implementation is based on aps_34idc beamline.

        :param scan_info: info allowing detector to retrieve data for a scan
        :return: corrected data array
        """
        frames_files = {}

        for file_name in os.listdir(scan_info):
            if file_name.endswith('tif'):
                fnbase = file_name[:-4]
            else:
                continue
            # for aps_34idc the file names end with the slice number, followed by 'tif' extension
            last_digits = re.search(r'\d+$', fnbase)
            if last_digits is not None:
                key = int(last_digits.group())
                frames_files[key] = ut.join(scan_info, file_name)

        ordered_keys = sorted(list(frames_files.keys()))
        ordered_slices = [self.correct_frame(frames_files[k]) for k in ordered_keys]

        data = np.stack(ordered_slices, axis=-1)
        offset = [0, 0]

        if self.roi is not None:
            data, offset = self.get_roi_slice(data)

        if self.max_crop is not None:
            data, offset = self.get_max_crop_slice(data, offset)

        return data, offset


    @abstractmethod
    def correct_frame(self, frame):
        """
        Applies the correction for detector.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """


class ASI(aps1Detector):
    """
    Subclass of Detector. Encapsulates any detector. Values are based on "34idcTIM2" detector.
    """
    name = "ASI"
    dims = (518, 518)
    det_roi = (0, 518, 0, 518)
    pixel = (55.0e-6, 55e-6)
    pixelorientation = ('x+', 'y-')  # in xrayutilities notation
    whitefield = None
    beam_zero = [dims[0] // 2, dims[1] // 2]

    def __init__(self, params):
        super(ASI, self).__init__(params)
        # The detector attributes specific for the detector.
        # Can include data directory, whitefield_filename, etc.

        # keep parameters that are relevant to the detector
        self.data_dir = params.get('data_dir')
        if 'whitefield_filename' in params:
            self.whitefield = ut.read_tif(params.get('whitefield_filename'))
            # the code below is specific to ASI detector
            self.wfavg = np.average(self.whitefield)
            self.wfstd = np.std(self.whitefield)
            self.whitefield = np.where(self.whitefield < self.wfavg - 3 * self.wfstd, 0, self.whitefield)
            self.Imult = params.get('Imult', self.wfavg)
        # min_frames, exclude_scanc, roi, max_crop are saved in common.det.Detectors superclass


    def correct_frame(self, frame_filename):
        """
        Applies correction for the detector.

        For ASI detector apply whitefield.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """
        frame = ut.read_tif(frame_filename)

        if self.whitefield is not None:
            frame = frame / self.whitefield * self.Imult
        else:
            # print('whitefield_filename not given, not correcting')
            pass

        frame = np.where(np.isfinite(frame), frame, 0)

        return frame

    @staticmethod
    def check_mandatory_params(params):
        """
        For the ASI detector the data directory is mandatory parameter.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """
        if  'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for 34idcTIM2 detector.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory {data_dir} does not exist.'
            raise ValueError(msg)


class BSE(aps1Detector):
    """
    Subclass of Detector. Encapsulates any detector. Values are based on "34idcTIM2" detector.
    """
    name = "BSE"
    dims = (4096, 4096)
    det_roi = [0, 4096, 0, 4096]
    pixel = (7.8e-6, 7.8e-6)
    pixelorientation = ('x-', 'y-')  # in xrayutilities notation
    whitefield = None
    darkfield = None
    beam_zero = [dims[0] // 2, dims[1] // 2]

    def __init__(self, params):
        super(BSE, self).__init__(params)
        # The detector attributes specific for the detector.
        # Can include data directory, whitefield_filename, etc.
        # keep parameters that are relevant to the detector
        self.data_dir = params.get('data_dir', None)
        if 'darkfield_filename' in params:
           self.darkfield = ut.read_tif(params.get('darkfield_filename')).astype(np.int32)
        # min_frames, exclude_scanc, roi, max_crop are saved in common.det.Detectors superclass


    def correct_frame(self, frame_filename):
        """
        Applies correction for the detector.

        This example is based on aps_34idc beamline, TIM2 detector and applies darkfield, whitefield.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """
        frame = ut.read_tif(frame_filename).astype(np.int32)

        if self.darkfield is not None:
            frame = self.darkfield - frame

        return frame

    @staticmethod
    def check_mandatory_params(params):
        """
        For the ASI detector the data directory is mandatory parameter.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """
        if  'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for 34idcTIM2 detector.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory {data_dir} does not exist.'
            raise ValueError(msg)


dets = {detector.name: detector for detector in aps1Detector.__subclasses__()}

def create_detector(det_name, params):
   return dets[det_name](params)


def check_mandatory_params(det_name, params):
    return dets[det_name].check_mandatory_params(params)

