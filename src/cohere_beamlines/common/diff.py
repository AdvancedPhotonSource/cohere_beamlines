import numpy as np
from abc import ABC, abstractmethod
import math as m
import xrayutilities.experiment as xuexp
import xrayutilities.utilities_noconf as xutilnoconf


class Diffractometer(ABC):
    """
    Abstract class representing diffractometer. It keeps fields related to the specific diffractometer represented by
    a subclass.

    diff_name : str
        diffractometer name
    """

    def __init__(self, params):
        # configuration parameters from config_instr
        self.params = params

    @abstractmethod
    def parse_metadata(self, scan):
        pass


    def convert_units(self, params):
        """
        Converts parameters to metric units. If needs conversion it should be implemented in the subclass.
        :return: converted parameters
        """
        return params


    def check_params(self, params):
        if 'detector' not in params:
            print('detector name not parsed from metadata and not configured')
            raise KeyError('detector name not parsed from metadata and not configured')
        if self.detectordist_mne not in params:
            print('detdist not parsed from metadata and not configured')
            raise KeyError('detdist not parsed from metadata and not configured')
        if 'scanmot' not in params:
            print('scanmot not parsed from metadata and not configured')
            raise KeyError('scanmot not parsed from metadata and not configured')
        if 'energy' not in params:
            print('energy not parsed from metadata and not configured')
            raise KeyError('energy not parsed from metadata and not configured')
        if 'scanmot_posns' not in params:
            print('scanmot_posns not parsed from metadata and not configured')
            raise KeyError('scanmot_posns not parsed from metadata and not configured')
        for ax in self.sampleaxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from metadata and not configured')
                raise KeyError(f'{ax} not parsed from metadata and not configured')
        for ax in self.detectoraxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from metadata and not configured')
                raise KeyError(f'{ax} not parsed from metadata and not configured')


    def get_q2(self, scan, slices, roi, det):
        """
        Returns q2 associated with the area on detector pointed by roi for requested slices.

        :param scan: int, scan number
        :param conf_params: conf_params dict
        :param slices: list containing slices numbers that the q2 vector will be calculated for
                        or 'all' for all slices
        :param roi: list defining roi (start, end, start, end)
        :param det: detector object
        :return: array, q2
        """
        params = self.parse_metadata(scan)
        # override with config params if any
        params.update(self.params)
        # exception is raised if missing parameter
        self.check_params(params)
        params = self.convert_units(params)
        energy = params['energy']
        enfix = 1
        if m.floor(m.log10(energy)) < 3:
            enfix = 1000
        params['energy'] = energy * enfix  # x-ray energy in eV

        scanmot = params['scanmot'].strip()
        # not sure this works anymore.  We need an energy scan for testing.
        if scanmot == 'en':
            scanen = np.array((energy, energy + params['scanmot_del'] * enfix))
        else:
            scanen = np.array((energy,))

        # define scan_mot array for the slices
        scanmot_posns = params['scanmot_posns']
        if slices == 'all':
            scanmot_arr = np.array(scanmot_posns)
        else:
            scanmot_arr = np.array([scanmot_posns[slice] for slice in slices])
        args = []
        for sa in self.sampleaxes_mne:
            if sa == params['scanmot']:
                args.append(scanmot_arr)
            else:
                args.append(params[sa])
        for da in self.detectoraxes_mne:
            args.append(params[da])
        qc = xuexp.QConversion(self.sampleaxes, self.detectoraxes, self.incidentaxis, en=scanen)
        # This is line from code in xrautilities. The parameters det.dims[0] and det.dims[1]
        # will be overridden by roi.
        # self._area_roi = kwargs.get("roi", [0, self._area_Nch1, 0, self._area_Nch2])
        qc.init_area(det.pixelorientation[0], det.pixelorientation[1],
                     det.get_beamzero()[0], det.get_beamzero()[1],
                     0, 0,  # the values are ignored if roi is given
                     distance=params[self.detectordist_mne],
                     pwidth1=det.pixel[0], pwidth2=det.pixel[1],
                     roi=roi)

        # q2 will always be (3,N,detroi1,detroi3) (vec, scanarr, Npx, Npy)
        q2 = np.squeeze(np.array(qc.area(*args, deg=True)))
        return q2, qc, params


    def get_pixelQ(self, pixel, scan, det):
        """
        Gets the Q value for a given pixel and slice in scan.

        :param pixel: tuple, (px, py) pixel coordinates
        :param scan: int, scan number
        :param det: Detector object
        :return: tuple, (qx, qy, qz) in inverse nm
        """
        # realpixelpos needs to correct for the relative pixel position in the roi.
        realpix = det.get_realpixelpos(pixel)
        # xrayuntilties needs (start, end, start, end) so convert to that.
        roi = [realpix[0], realpix[0] + 1, realpix[1], realpix[1] + 1]
        slices = [pixel[2]] # q2 vector for slice with max intensity
        q2, qc, params = self.get_q2(scan, slices, roi, det)

        # transform to lab coords from sample reference frame
#        params[params['scanmot']] = params['scanmot_posns'][pixel[2]]
        q3 = qc.transformSample2Lab(q2, *[params[x] for x in self.sampleaxes_mne]) * 10.0  # convert to inverse nm.
        return q3


    def get_RSM(self, scan, det):
        det_roi = det.get_det_roi()
        slices = 'all' # q2 vector for all slices

        q2, qc, params = self.get_q2(scan, slices, det_roi, det)

        # transform to lab coords from sample reference frame
        q3 = qc.transformSample2Lab(q2.transpose(1,2,3,0), *[params[x] for x in self.sampleaxes_mne]) * 10.0  # convert to inverse nm.

        return q3.transpose(1,2,0,3) #in order to match tiff in paraview.  Since paraview does not transpose on read the way we do.


    def get_geometry(self, max_ind, scan, conf_params, det, **kwargs):
        """
        Calculates geometry based on diffractometer and detector attributes and experiment parameters for given scan.

        Typically, the metadata such as detector axes, sample axes, camera distance, energy are parsed in a manner
        specific to the beamline. The parsed values can be overridden by configuration.

        :param shape: tuple, shape of array
        :param scan: scan the geometry is calculated for
        :param conf_params: configuration parameters
        :return: tuple, geometry information
        """
        binning = conf_params.get('binning', [1, 1, 1])
        # adjust max_ind for binning
        roi = [max_ind[0] // binning[0] - 1, max_ind[0] // binning[0] + 1,
               max_ind[1] // binning[1] - 1, max_ind[1] // binning[1] + 1]

        # assume max in the middle slice
        slices = [max_ind[2] // binning[2], max_ind[2] // binning[2] + binning[2]]
        det.pixel = list(det.pixel)
        det.pixel[0] = det.pixel[0] * binning[0]
        det.pixel[1] = det.pixel[1] * binning[1]

        q2, qc, params = self.get_q2(scan, slices, roi, det)

        Astar = q2[:, 0, 1, 0] - q2[:, 0, 0, 0]
        Bstar = q2[:, 0, 0, 1] - q2[:, 0, 0, 0]
        Cstar = q2[:, 1, 0, 0] - q2[:, 0, 0, 0]

        xtal = kwargs.get('xtal', False)
        if xtal:
            Trecip_cryst = np.zeros(9)
            Trecip_cryst.shape = (3, 3)
            Trecip_cryst[:, 0] = Astar * 10
            Trecip_cryst[:, 1] = Bstar * 10
            Trecip_cryst[:, 2] = Cstar * 10
            return Trecip_cryst, None

        # transform to lab coords from sample reference frame
        Astar = qc.transformSample2Lab(Astar, *[params[x] for x in self.sampleaxes_mne]) * 10.0  # convert to inverse nm.
        Bstar = qc.transformSample2Lab(Bstar, *[params[x] for x in self.sampleaxes_mne]) * 10.0
        Cstar = qc.transformSample2Lab(Cstar, *[params[x] for x in self.sampleaxes_mne]) * 10.0

        denom = np.dot(Astar, np.cross(Bstar, Cstar))
        A = 2 * m.pi * np.cross(Bstar, Cstar) / denom
        B = 2 * m.pi * np.cross(Cstar, Astar) / denom
        C = 2 * m.pi * np.cross(Astar, Bstar) / denom

        Trecip = np.zeros(9)
        Trecip.shape = (3, 3)
        Trecip[:, 0] = Astar
        Trecip[:, 1] = Bstar
        Trecip[:, 2] = Cstar

        Tdir = np.zeros(9)
        Tdir.shape = (3, 3)
        Tdir = np.array((A, B, C)).transpose()

        wl = xutilnoconf.en2lam(params['energy'])
        kf = qc.getDetectorPos(*[params[x] for x in self.detectoraxes_mne],
                               deg=True)  # return in meters.  Not K as docs say.
        kf_hat = kf / np.linalg.norm(kf)
        ki = self.incidentaxis
        ki_hat = ki / np.linalg.norm(ki)
        ki = 2 * np.pi / wl * ki_hat
        kf = 2 * np.pi / wl * kf_hat
        myq = kf - ki

        return (Trecip, Tdir, myq, ki, kf)
