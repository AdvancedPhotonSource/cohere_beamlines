# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
import numpy as np
import cohere_core.utilities as ut
from abc import ABC, abstractmethod
import h5py


class Detector(ABC):
    """
    Class representing detector.

    Some functions are common for all detectors and are implemented in the base class.
    """

    def __init__(self, name):
        self.name = name

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
                scan = int(scanfile[:-3].split('_')[-1])
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
                        self.whitefield = whitefield[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
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
                        self.darkfield = darkfield[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
                        self.darkfield = np.where(self.darkfield > 0, 0.0, 1.0)
                        if self.whitefield is not None:
                                self.whitefield = self.darkfield * self.whitefield  # kill known bad pixel
                except:
                    pass

        # apply roi
        arr = arr[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3], :]
        arr = self.correct(arr)

        if self.max_crop is not None:
            def isOnedge(maxindx):
                onedge = False
                for i in range(len(maxindx)):
                    if maxindx[i] == 0 or maxindx[i] > arr.shape[i] - 1:
                        onedge = True
                        break
                return onedge

            # check if the max value is bad pixel. If so zero it and get the next max value.
            maxindx = np.unravel_index(arr.argmax(), arr.shape)
            while ( isOnedge(maxindx) or
                    arr[maxindx[0] + 1, maxindx[1], maxindx[2]] == 0
                   and arr[maxindx[0] - 1, maxindx[1], maxindx[2]] == 0
                   or arr[maxindx[0], maxindx[1] + 1, maxindx[2]] == 0
                   and arr[maxindx[0], maxindx[1] - 1, maxindx[2]] == 0):
                arr[maxindx] = 0.0
                maxindx = np.unravel_index(arr.argmax(), arr.shape)

            mc0 = self.max_crop[0] // 2
            mc1 = self.max_crop[1] // 2
            cropslice0 = slice(max(0, maxindx[0] - mc0), min(maxindx[0] + mc0, arr.shape[0]))
            cropslice1 = slice(max(0, maxindx[1] - mc1), min(maxindx[1] + mc1, arr.shape[1]))
            arr = arr[cropslice0, cropslice1, :]

        return arr

    @abstractmethod
    def correct(self, frame):
        """
        Applies the correction for detector.

        :param frame: 2D raw data file representing a frame
        :return: corrected frame
        """

class ASI(Detector):
    """
    Subclass of Detector. Encapsulates any detector. Values are based on "34idcTIM2" detector.
    """
    name = "ASI"
    roi = (0, 512, 0, 512)
    pixel = (55.0e-6, 55e-6)
    pixelorientation = ('x+', 'y-')  # in xrayutilities notation
    whitefield = None
    darkfield = None
    max_crop = None
    min_frames = None  # defines minimum frame scans in scan directory
    Imult = None

    def __init__(self, params):
        super(ASI, self).__init__(self.name)
        # The detector attributes specific for the detector.
        # Can include data directory, whitefield_filename, roi, etc.
        # keep parameters that are relevant to the detector
        self.data_dir = params.get('data_dir')
        self.roi = params.get('roi', ASI.roi)
        self.Imult = params.get('Imult', ASI.Imult)
        # init darkfield and whitefield if given
        if 'whitefield_filename' in params:
            self.whitefield = ut.read_tif(params.get('whitefield_filename'))[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
            # the code below is specific to ASI detector
            self.wfavg = np.average(self.whitefield)
            self.wfstd = np.std(self.whitefield)
            self.whitefield = np.where(self.whitefield < self.wfavg - 3 * self.wfstd, 0, self.whitefield)
            self.Imult = params.get('Imult', self.wfavg)

        if 'darkfield_filename' in params:
            self.darkfield = ut.read_tif(params.get('darkfield_filename'))[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
            self.darkfield = np.where(self.darkfield > 0, 0.0, 1.0)
            if self.whitefield is not None:
                    self.whitefield = self.darkfield * self.whitefield  # kill known bad pixel
        self.min_frames = params.get('min_frames', None)
        self.exclude_scans = params.get('exclude_scans', [])
        self.max_crop = params.get('max_crop', None)


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


class BSE(Detector):
    """
    Subclass of Detector. Encapsulates any detector. Values are based on "34idcTIM2" detector.
    """
    name = "BSE"
    roi = (0, 4096, 0, 4096)
    pixel = (7.8e-6, 7.8e-6)
    pixelorientation = ('x-', 'y-')  # in xrayutilities notation
    whitefield = None
    darkfield=None

    def __init__(self, params):
        super(BSE, self).__init__(self.name)
        # The detector attributes specific for the detector.
        # Can include data directory, whitefield_filename, roi, etc.
        # keep parameters that are relevant to the detector
        self.data_dir = params.get('data_dir')
        self.roi = params.get('roi', BSE.roi)
        if 'darkfield_filename' in params:
            self.darkfield = ut.read_tif(params.get('darkfield_filename'))[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
            self.darkfield = np.where(self.darkfield > 0, 0.0, 1.0)
        self.min_frames = params.get('min_frames', None)
        self.exclude_scans = params.get('exclude_scans', [])
        self.max_crop = params.get('max_crop', None)


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


def create_detector(det_name, params):
    for detector in Detector.__subclasses__():
        if detector.name == det_name:
            return detector(params)
    msg = f'detector {det_name} not defined'
    raise ValueError(msg)


dets = {detector.name: detector for detector in Detector.__subclasses__()}

def get_pixel(det_name):
    return dets[det_name].pixel


def get_pixel_orientation(det_name):
    return dets[det_name].pixelorientation


def check_mandatory_params(det_name, params):
    for detector in Detector.__subclasses__():
        if detector.name == det_name:
            return dets[det_name].check_mandatory_params(params)
    msg = f'detector {det_name} not defined'
    raise ValueError(msg)