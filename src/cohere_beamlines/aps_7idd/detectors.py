# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import numpy as np
import os
import re
import cohere_core.utilities as ut
from cohere_beamlines.beam_detectors.common_det import Detector
from abc import abstractmethod

class aps7Detector(Detector):
    """
    Abstract class representing detector.
    """

    def __init__(self, params):
        super(aps7Detector, self).__init__(params)


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

        # check for directories
        for scandir in sorted(os.listdir(self.data_dir)):
            scandir_full = ut.join(self.data_dir, scandir)
            if os.path.isdir(scandir_full):
                last_digits = re.search(r'\d+$', scandir)
                if last_digits is not None:
                    scan = int(last_digits.group())
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

        # remove empty sub-lists
        scans_dirs_ranges = [e for e in scans_dirs_ranges if len(e) > 0]
        return scans_dirs_ranges


    def get_scan_array(self, scan_info):
        """
        Reads/loads raw data file and applies correction.

        Reads raw data from a directory. The directory name is scan_info. The raw data is in form of 2D
        frames. The frames are read, corrected and stocked into 3D data

        :param scan_info: directory where the detector to retrieve data for a scan
        :return: corrected data array
        """
        slices_files = {}
        for file_name in os.listdir(scan_info):
            if file_name.endswith('tif'):
                fnbase = file_name[:-4]
            else:
                continue
            # for aps_34idc the file names end with the slice number, followed by 'tif' extension
            last_digits = re.search(r'\d+$', fnbase)
            if last_digits is not None:
                key = int(last_digits.group())
                slices_files[key] = ut.join(scan_info, file_name)

        ordered_keys = sorted(list(slices_files.keys()))
        ordered_frames = [ut.read_tif(slices_files[key]) for key in ordered_keys]
#        ordered_slices = [self.correct_frame(slices_files[k]) for k in ordered_keys]

        data = np.stack(ordered_frames, axis=-1)[self.slice]

        if self.user_roi is not None:
            data = self.get_user_roi_slice(data)

        data = self.correct(data)

        if self.max_crop is not None:
            data = self.get_max_crop_slice(data)

        return data


    @abstractmethod
    def check_mandatory_params(self, params):
        """
        checks if all mandatory parameters are in params.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """


    @abstractmethod
    def correct(self, frame):
        """
        Applies the correction for detector.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """


class Detector_7iddrobot(aps7Detector):
    """
    Subclass of Detector. Encapsulates "34idcTIM1" detector.
    """
    name = "7iddrobot"
    roi = [0, 1062, 0, 1028]
    pixel = (75.0e-6, 75e-6)
    pixelorientation = ('y+', 'x+')  # in xrayutilities notation
    darkfield = None
    data_dir = None
    Imult = 1.0

    def __init__(self, params):
        super(Detector_7iddrobot, self).__init__(params)
        # The detector attributes for background/whitefield/etc need to be set to read frames
        # this will capture things like data directory, darkfield_filename, etc.
        self.data_dir = params.get('data_dir') # mandatory
        roi = params.get('roi', Detector_7iddrobot.roi)
        # slices reflect transposed data
        self.roi_slice = np.s_[roi[0]:roi[0] + roi[1], roi[2]:roi[2] + roi[3]]
        self.slice = np.s_[roi[0]:roi[0] + roi[1], roi[2]:roi[2] + roi[3], :]
        if 'darkfield_filename' in params:
            self.darkfield = ut.read_tif(params.get('darkfield_filename'))[self.roi_slice]


    # TIM1 only needs bad pixels deleted.  Even that is optional.
    def correct(self, data):
        """
        Reads raw frame from a file, and applies correction for 34idcTIM1 detector, i.e. darkfield.
        Parameters
        ----------
        filename : str
            slice data file name
        Returns
        -------
        frame : ndarray
            frame after correction
        """
        if self.darkfield is not None:
            if len(self.darkfield.shape) == 2:
                cor = self.darkfield[:,:,np.newaxis]
            else:
                cor = self.darkfield
            data = data * cor

        return data


    @staticmethod
    def check_mandatory_params(params):
        """
        For the 34idcTIM1 detector the data directory is mandatory. The darkfield file is optional.

        :return: message indicating problem or empty message if all is ok
        """
        if  'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for 34idcTIM1 detector.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory{data_dir} does not exist.'
            raise ValueError(msg)



dets = {detector.name: detector for detector in aps7Detector.__subclasses__()}

def create_detector(det_name, params):
   return dets[det_name](params)


def get_pixel(det_name):
    return dets[det_name].pixel


def get_pixel_orientation(det_name):
    return dets[det_name].pixelorientation


def check_mandatory_params(det_name, params):
    return dets[det_name].check_mandatory_params(params)

