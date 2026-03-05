from abc import ABC, abstractmethod
import numpy as np

class Detector(ABC):
    """
    Abstract class representing detector.
    """

    def __init__(self, params):
        self.min_frames = params.get('min_frames', 0)
        self.exclude_scans = params.get('exclude_scans', [])
        self.roi = params.get('roi', None)
        if self.roi is not None:
            self.roi_format = params.get('roi_format')
        self.max_crop = params.get('max_crop', None)


    @abstractmethod
    def get_scan_array(self, scan_info):
        pass


    def get_roi_slice(self, data):
        """
        Crops the data to the size of roi. The roi is interpreted according to the roi_format.

        The supported formats:
        center point, distance : [center_point_x, center_point_y, distance_x, distance_y]
        start point, end point : [start_point_x, start_point_y, end_point_x, end_point_y]
        start point, distance : [start_point_x, distance_x, start_point_y, distance_y]')

        :param data:
        :param roi_format:
        :return:
        """
        roi = self.roi
        roi_format = self.roi_format
        shape = data.shape
        if roi_format == "center_point_dist":
            [center_point_x, center_point_y, distance_x, distance_y] = roi
            half_dist_x = distance_x // 2
            half_dist_y = distance_y // 2
            slice_start_x = max(0, center_point_x - half_dist_x)
            slice_end_x = min(shape[0], slice_start_x + distance_x)
            slice_start_y = max(0, center_point_y - half_dist_y)
            slice_end_y = min(shape[1], slice_start_y + distance_y)
            cropslice0 = slice(slice_start_x, slice_end_x)
            cropslice1 = slice(slice_start_y, slice_end_y)
        elif roi_format == "start_point_end_point":
            [start_point_x, start_point_y, end_point_x, end_point_y] = roi
            cropslice0 = slice(start_point_x, end_point_x)
            cropslice1 = slice(start_point_y, end_point_y)
        elif roi_format == "start_point_dist":
            [start_point_x, start_point_y, distance_x, distance_y] = roi
            cropslice0 = slice(start_point_x, min(start_point_x + distance_x, shape[0]))
            cropslice1 = slice(start_point_y, min(start_point_y + distance_y, shape[1]))
        else:
            raise ValueError("Unknown roi format: {}".format(roi_format))

        return data[cropslice0, cropslice1, :]


    def get_max_crop_slice(self, data):
        """
        Crops the data to the size of max_crop with the maximum in the center.

        The max_crop defines x and y axes (frame). The z axis is not changed.
        If the maximum value is closer to the edge of the frame than the half of max_crop, then the output
        array is smaller than max_crop.
        If the max value is a bad pixel, the bad pixel is set to 0 across all frames.
        To determine bad pixel the code checks neighbour values, and if both across x axis or both across y axis
        are 0, it is then bad pixel.

        :param data:
        :param max_crop:
        :return:
        """
        max_crop = self.max_crop
        shape = data.shape

        def is_onedge(maxindx):
            if maxindx[0] == 0 or maxindx[0] == shape[0] - 1:
                return True
            if maxindx[1] == 0 or maxindx[1] == shape[1] - 1:
                return True
            return False

        # check if the max value is bad pixel. If so zero it and get the next max value.
        maxindx = np.unravel_index(data.argmax(), data.shape)
        while (is_onedge(maxindx) or
               data[maxindx[0] + 1, maxindx[1], maxindx[2]] == 0
               and data[maxindx[0] - 1, maxindx[1], maxindx[2]] == 0
               or data[maxindx[0], maxindx[1] + 1, maxindx[2]] == 0
               and data[maxindx[0], maxindx[1] - 1, maxindx[2]] == 0):
            # zero out bad point in all frames
            data[maxindx[0], maxindx[1], :] = 0.0
            maxindx = np.unravel_index(data.argmax(), shape)

        mc0 = max_crop[0] // 2
        mc1 = max_crop[1] // 2
        cropslice0 = slice(max(0, maxindx[0] - mc0), min(maxindx[0] + mc0, shape[0]))
        cropslice1 = slice(max(0, maxindx[1] - mc1), min(maxindx[1] + mc1, shape[1]))
        return data[cropslice0, cropslice1, :]

