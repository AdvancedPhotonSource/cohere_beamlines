# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import numpy as np
import h5py
from cohere_beamlines.common.det import Detector
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

        # apply correction if needed
        # the rdata already is corrected

        offset = [0, 0]

        if self.roi is not None:
            data, offset = self.get_roi_slice(data)

        if self.max_crop is not None:
            data, offset = self.get_max_crop_slice(data, offset)

        return data, offset


class Detector_mpxgaas(esrf1Detector):
    """
    Subclass of Detector. Encapsulates "mpxgaas" detector.
    """
    name = "mpxgaas"
    dims = (516, 516)
    det_roi = [0, 516, 0, 516]
    pixel = (55.0e-6, 55e-6)
    pixelorientation = ('x-', 'y-')  # in xrayutilities notation
    beam_zero = [dims[0] // 2, dims[1] // 2]

    def __init__(self, conf_params):
        super(Detector_mpxgaas, self).__init__(conf_params)

        self.h5file = conf_params.get("h5file")
        # # min_frames, exclude_scanc, roi, max_crop are saved in common.det.Detectors superclass


dets = {detector.name: detector for detector in esrf1Detector.__subclasses__()}

def create_detector(det_name, params):
   return dets[det_name](params)


def check_mandatory_params(det_name, params):
    return dets[det_name].check_mandatory_params(params)
