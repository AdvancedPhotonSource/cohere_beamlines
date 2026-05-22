from abc import ABC, abstractmethod
import numpy as np

class Detector(ABC):
    """
    Abstract class representing detector.
    """
    # list of detectors that may use remove_horizontal_band_background
    det_bound_background = ['BSE']

    def __init__(self, params):
        self.min_frames = params.get('min_frames', 0)
        self.exclude_scans = params.get('exclude_scans', [])
        self.roi = params.get('roi', None)
        if self.roi is not None:
            roi_format = params.get('roi_format', None)
            if roi_format is None:
                raise ValueError('roi_format must be specified')
            # translate roi to the same format: 'start_point_dist'
            # [start_point_x, distance_x, start_point_y, distance_y] = roi
            if roi_format == "center_point_dist":
                [center_point_x, center_point_y, distance_x, distance_y] = self.roi
                start_point_x = max(0, center_point_x - distance_x // 2)
                start_point_y = max(0, center_point_y - distance_y //2)
                self.roi = [start_point_x, distance_x, start_point_y, distance_y]
            elif roi_format == "start_point_end_point":
                [start_point_x, start_point_y, end_point_x, end_point_y] = self.roi
                distance_x = end_point_x - start_point_x
                distance_y = end_point_y - start_point_y
                self.roi = [start_point_x, distance_x, start_point_y, distance_y]
            elif roi_format != "start_point_dist":
                raise ValueError(f'roi_format {roi_format} not supported')
        self.max_crop = params.get('max_crop', None)
        self.min_frames = params.get('min_frames', 0)
        self.exclude_scans = params.get('exclude_scans', [])
        self.beam_zero = params.get('beam_zero', self.beam_zero)
        # logic for removing bound background
        if self.name in self.det_bound_background:
            self.remove_band_background = params.get('remove_band_background', False)
            if self.remove_band_background:
                if 'rbb_smooth_sigma' in params:
                    self.rbb_smooth_sigma = params.get('rbb_smooth_sigma', self.rbb_smooth_sigma)
                if 'rbb_robust' in params and params['rbb_robust']:
                    self.rbb_robust = params['rbb_robust']
        self.darkfield = None
        self.whitefield = None

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
        shape = data.shape
        [start_point_x, distance_x, start_point_y, distance_y] = roi
        cropslice0 = slice(start_point_x, min(start_point_x + distance_x, shape[0]))
        cropslice1 = slice(start_point_y, min(start_point_y + distance_y, shape[1]))

        offset = [start_point_x, start_point_y]

        if self.darkfield is not None:
            self.darkfield = self.darkfield[cropslice0, cropslice1]
        if self.whitefield is not None:
            self.whitefield = self.whitefield[cropslice0, cropslice1]

        return data[cropslice0, cropslice1, :], offset


    def get_max_crop_slice(self, data, offset):
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
        offset[0] = offset[0] + max(0, maxindx[0] - mc0)
        offset[1] = offset[1] + max(0, maxindx[1] - mc1)
        return data[cropslice0, cropslice1, :], offset


    def get_beamzero(self):
        return self.beam_zero


    def get_realpixelpos(self, pixel):
        return pixel


    # Could be overridden in detector class.
    def get_det_roi(self):
        return self.det_roi


    def remove_horizontal_band_background(self,
            stack,
            smooth_sigma,  # smoothing along x to avoid removing real features
            robust = True,
    ):
        """
        Remove time-varying horizontal banding (row-wise background) from a stack.

        Assumes banding is mostly a function of row (y): each frame has stripes that are
        approximately constant across columns, possibly slowly varying along columns.

        Parameters
        ----------
        stack : (T,Y,Z) array
        smooth_sigma : float
            Std-dev for 1D Gaussian smoothing of the estimated row profile along x.
            Higher = smoother background estimate (safer for preserving objects).
        robust : bool
            If True, estimate row profile using median across columns (robust to objects).
            If False, use mean.
        """
        if self.name not in Detector.det_bound_background:
            raise ValueError("removal of horizontal bound background does not apply to detector '{}'".format(self.name))

        if stack.ndim != 3:
            raise ValueError("stack must be (Y, X, T)")

        stack_f = stack.astype(np.float32, copy=False)
        Y, X, T = stack_f.shape

        # 1) Estimate per-frame row profile: bg_row[x,t] ~ median_x I[y,x,t]
        if robust:
            bg_row = np.median(stack_f, axis=0)  # (X,T)
        else:
            bg_row = np.mean(stack_f, axis=0)  # (X,T)

        # 2) Expand to full image as stripes constant across x
        bg = bg_row[None, :, :] * np.ones((Y, 1, 1), dtype=np.float32)

        # 3) Optional: allow slow variation along x by smoothing the residual field
        #    If your stripes are not perfectly constant across x, estimate a low-pass 2D bg:
        #    Here we smooth only along x (axis=2) to keep "horizontal pattern" character.
        if smooth_sigma and smooth_sigma > 0:
            # FFT-based Gaussian smoothing along x for speed (works well for large X)
            y = np.fft.rfftfreq(Y)
            gauss = np.exp(-(2 * (np.pi ** 2)) * (smooth_sigma ** 2) * (y ** 2)).astype(np.float32)  # (X//2+1,)
            # Smooth each (t,y,:) row in frequency domain
            bg_fft = np.fft.rfft(bg, axis=0)
            bg_fft *= gauss[:, None, None]
            bg = np.fft.irfft(bg_fft, n=Y, axis=0).astype(np.float32)

        corrected = stack_f - bg
        return corrected.astype(np.float32)  # , bg.astype(np.float32)
