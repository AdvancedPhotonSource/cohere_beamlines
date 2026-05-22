import os
from abc import ABC, abstractmethod
import pandas as pd
import cohere_core.utilities as ut

class Instrument(ABC):
    """
      This class encapsulates istruments: diffractometer and detector used for that experiment.
      It provides interface to get the classes encapsulating the diffractometer and detector.
    """

    def __init__(self, det_obj, diff_obj, main_conf):
        """
        Constructor

        :param det_obj: detector object, can be None
        :param diff_obj: diffractometer object, can be None
        """
        self.det_obj = det_obj
        self.diff_obj = diff_obj
        self.main_conf = main_conf

    @abstractmethod
    def datainfo4scans(self):
        pass

    @abstractmethod
    def get_geometry(self, max_ind, scan, conf_maps, **kwargs):
        pass

    def get_metadata(self, scan):
        return self.diff_obj.parse_metadata(scan)

    def get_scan_array(self, scan_dir):
        return self.det_obj.get_scan_array(scan_dir)

    def get_RSM(self, scan):
        return self.diff_obj.get_RSM(scan, self.det_obj)

    def get_pixelQ(self, pixel, scan):
        return self.diff_obj.get_pixelQ(pixel, scan, self.det_obj)
