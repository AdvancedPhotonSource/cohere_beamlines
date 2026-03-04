# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import numpy as np
import h5py
from cohere_beamlines.beam_detectors.common_det import Detector
from cohere_core import data


class esrf1Detector(Detector):
    def __init__(self, params):
        super(esrf1Detector, self).__init__(params)


    def nodes4scans(self, scans):
        """
        Finds nodes in hdf5 file that correspond to given scans and scan ranges.

        Parameters
        ----------
        scans : list
            list of lists defining scan(s) and scan range(s), ordered
        h5file : str
            h5file containing the data
        Returns
        -------
        list
            a list of sublist, the sublist reflecting scan ranges or scans and containing tuples of existing scans
            and nodes where the data for this scan is located
        """
        scans_nodes_ranges = []
        for (start, stop) in scans:
            # todo add check
            scans_nodes_ranges.append([(i, f"{i}.1/measurement/{self.name}") for i in range(start, stop+1)if i not in self.exclude_scans])
        return scans_nodes_ranges


    def get_scan_array(self, node):
        """
        Reads raw rdata files from scan nodes, applies correction, and returns a dict with 3D corrected rdata
        for each node.
        Parameters
        ----------
        node : str
            node in hd5 file of scan to read the raw files from
        h5file : str
            h5file containing the rdata
        Returns
        -------
        arr : dict {str : ndarray}
            node : 3D array containing corrected rdata for one scan.
        """
        with h5py.File(self.h5file, "r") as h5f:
            data = h5f[node][:].T

        # # print max
        print('shape, max coordinates, max value', data.shape, np.unravel_index(np.argmax(data), data.shape), np.max(data))
        # apply correction if needed
        # the rdata already is corrected

        if self.user_roi is not None:
            data = self.get_user_roi_slice(data)

        if self.max_crop is not None:
            data = self.get_max_crop_slice(data)

        return data


class Detector_mpxgaas(esrf1Detector):
    """
    Subclass of Detector. Encapsulates "mpxgaas" detector.
    """
    name = "mpxgaas"
   # dims = (516, 516)
    pixel = (55.0e-6, 55e-6)
    pixelorientation = ('x-', 'y-')  # in xrayutilities notation


    def __init__(self, conf_params):
        super(Detector_mpxgaas, self).__init__(conf_params)
        for key, val in conf_params.items():
            if val is None:
                continue
            setattr(self, key, val)


dets = {detector.name: detector for detector in esrf1Detector.__subclasses__()}

def create_detector(det_name, params):
   return dets[det_name](params)


def get_pixel(det_name):
    return dets[det_name].pixel


def get_pixel_orientation(det_name):
    return dets[det_name].pixelorientation


def check_mandatory_params(det_name, params):
    return dets[det_name].check_mandatory_params(params)
