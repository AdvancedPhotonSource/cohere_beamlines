# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
import numpy as np
import cohere_core.utilities as ut
from cohere_beamlines.beam_detectors.common_det import Detector
from abc import abstractmethod
import h5py


class aps20Detector(Detector):
    """
    Class representing detector.

    Some functions are common for all detectors and are implemented in the base class.
    """

    def __init__(self, params):
        super(aps20Detector, self).__init__(params)

    def files4scans(self, scans):
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
        first_scan = scans[0][0]
        last_scan = scans[-1][-1]
        scans_files = {}
        for scanfile in sorted(os.listdir(self.data_dir)):
            scanfile_full = ut.join(self.data_dir, scanfile)
            if not os.path.isfile(scanfile_full) or not scanfile_full.endswith('.h5'):
                continue
            # chop off the ".h5" and get the scan number
            try:
                # scan = int(scanfile[:-3].split('_')[-1])
                scan = int(scanfile.split('.')[0].split('_')[-1])
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
                    if h5f['exchange/data'].shape[0] < self.min_frames:
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
        Reads/loads raw data file and applies correction. The correction is detector dependent.

        Reads raw data from a directory. The directory name is scan_info. The raw data is in form of 2D
        frames. The frames are read, corrected and stocked into 3D data
        This implementation is based on aps_34idc beamline.

        :param scan_info: info allowing detector to retrieve data for a scan
        :return: corrected data array
        """
        h5file = scan_info
        with h5py.File(h5file, "r") as h5f:
            arr = h5f['exchange/data'][:].T
            if self.whitefield is None:
                # the whitefield was not configured, try to read it from h5 file
                try:
                    whitefield = h5f['exchange/data_white'][:].T
                    if np.sum(whitefield) > 0:
                        self.whitefield = whitefield
                        # the code below is specific to ASI detector
                        self.wfavg = np.average(self.whitefield)
                        self.wfstd = np.std(self.whitefield)
                        self.whitefield = np.where(self.whitefield < self.wfavg - 3 * self.wfstd, 0, self.whitefield)
                        if self.Imult is None:
                            self.Imult = self.wfavg
                except:
                    pass
            if self.darkfield is None:
                # the darkfield was not configured, try to read it from h5 file
                try:
                    darkfield = h5f['exchange/data_dark'][:].T
                    if np.sum(whitefield) > 0:
                        self.darkfield = darkfield
                        self.darkfield = np.where(self.darkfield > 0, 0.0, 1.0)
                        if self.whitefield is not None:
                                self.whitefield = self.darkfield * self.whitefield  # kill known bad pixel
                except:
                    pass

        arr = self.correct(arr)

        if self.roi is not None:
            arr = self.get_roi_slice(arr)

        if self.max_crop is not None:
            arr = self.get_max_crop_slice(arr)

        return arr


    @abstractmethod
    def correct(self, frame):
        """
        Applies the correction for detector.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """

class ASI(aps20Detector):
    """
    Subclass of Detector. Encapsulates any detector. Values are based on "34idcTIM2" detector.
    """
    name = "ASI"
    #dims = (512, 512)
    pixel = (55.0e-6, 55e-6)
    pixelorientation = ('x+', 'y-')  # in xrayutilities notation
    whitefield = None
    darkfield = None
    max_crop = None
    min_frames = 0  # defines minimum frame scans in scan directory
    Imult = None

    def __init__(self, params):
        super(ASI, self).__init__(params)
        # The detector attributes specific for the detector.
        # Can include data directory, whitefield_filename, etc.
        # keep parameters that are relevant to the detector
        self.data_dir = params.get('data_dir')
        self.Imult = params.get('Imult', ASI.Imult)
        # init darkfield and whitefield if given
        if 'whitefield_filename' in params:
            self.whitefield = ut.read_tif(params.get('whitefield_filename')).T
            self.whitefield = self.whitefield
            # the code below is specific to ASI detector
            self.wfavg = np.average(self.whitefield)
            self.wfstd = np.std(self.whitefield)
            self.whitefield = np.where(self.whitefield < self.wfavg - 3 * self.wfstd, 0, self.whitefield)
            self.Imult = params.get('Imult', self.wfavg)

        if 'darkfield_filename' in params:
            self.darkfield = ut.read_tif(params.get('darkfield_filename')).T
            self.darkfield = self.darkfield
            self.darkfield = np.where(self.darkfield > 0, 0.0, 1.0)
            if self.whitefield is not None:
                    self.whitefield = self.darkfield * self.whitefield  # kill known bad pixel


    def correct(self, data):
        """
        Applies correction for the detector.

        For ASI detector apply whitefield.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """
        if self.darkfield is not None:
            if len(self.darkfield.shape) == 2:
                cor = self.darkfield[:,:,np.newaxis]
            else:
                cor = self.darkfield
            data = data * cor

        if self.whitefield is not None:
            if len(self.whitefield.shape) == 2:
                cor = self.whitefield[:,:,np.newaxis]
            else:
                cor = self.whitefield
            data = data / cor * self.Imult
        else:
            pass

        data = np.nan_to_num(data)

        return data

    @staticmethod
    def check_mandatory_params(params):
        """
        For the ASI detector the data directory is mandatory parameter.

        :params: parameters needed to create detector
        :return: message indicating problem or empty message if all is ok
        """
        if 'data_dir' not in params:
            msg = 'data_dir parameter not configured, mandatory for 34idcTIM2 detector.'
            raise ValueError(msg)
        data_dir = params['data_dir']
        if not os.path.isdir(data_dir):
            msg = f'data_dir directory {data_dir} does not exist.'
            raise ValueError(msg)


class BSE(aps20Detector):
    """
    Subclass of Detector. Encapsulates any detector. Values are based on "34idcTIM2" detector.
    """
    name = "BSE"
    #dims = (4096, 4096)
    pixel = (7.8e-6, 7.8e-6)
    pixelorientation = ('x-', 'y-')  # in xrayutilities notation
    whitefield = None
    darkfield=None
    rbb_smooth_sigma = 50

    def __init__(self, params):
        super(BSE, self).__init__(params)
        # The detector attributes specific for the detector.
        # Can include data directory, whitefield_filename, etc.
        # keep parameters that are relevant to the detector
        self.data_dir = params.get('data_dir')
        if 'darkfield_filename' in params:
            self.darkfield = ut.read_tif(params.get('darkfield_filename')).T
            self.darkfield = self.darkfield
            self.darkfield = np.where(self.darkfield > 0, 0.0, 1.0)


    def correct(self, data):
        """
        Applies correction for the detector.

        This example is based on aps_34idc beamline, TIM2 detector and applies darkfield, whitefield.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """
        if self.darkfield is not None:
            if len(self.darkfield.shape) == 2:
                cor = self.darkfield[:,:,np.newaxis]
            else:
                cor = self.darkfield
            data = data * cor

        if self.whitefield is not None:
            if len(self.whitefield.shape) == 2:
                cor = self.whitefield[:,:,np.newaxis]
            else:
                cor = self.whitefield
            data = data / cor * self.Imult
        else:
            pass

        data = np.nan_to_num(data)
        self.rbb(data)
        return data


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


dets = {detector.name: detector for detector in aps20Detector.__subclasses__()}

def create_detector(det_name, params):
   return dets[det_name](params)


def get_pixel(det_name):
    return dets[det_name].pixel


def get_pixel_orientation(det_name):
    return dets[det_name].pixelorientation


def check_mandatory_params(det_name, params):
    return dets[det_name].check_mandatory_params(params)
