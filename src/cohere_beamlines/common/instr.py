from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import math as m
import xrayutilities.experiment as xuexp
import xrayutilities.utilities_noconf as xutilnoconf

class Instrument(ABC):
    """
      This class encapsulates istruments: diffractometer and detector used for that experiment.
      It provides interface to get the classes encapsulating the diffractometer and detector.
    """

    def __init__(self, det_obj, diff_obj, conf_params):
        """
        Constructor

        :param det_obj: detector object, can be None
        :param diff_obj: diffractometer object, can be None
        """
        self.det_obj = det_obj
        self.diff_obj = diff_obj
        self.conf_params = conf_params


    @abstractmethod
    def datainfo4scans(self):
        pass


    def convert_units(self, params):
        """
        Converts to metric units. May be overridden.
        :return:
        """
        return params


    def get_scan_array(self, scan_dir):
        return self.det_obj.get_scan_array(scan_dir)


    @abstractmethod
    def parse_metadata(self, scan):
        pass


    def check_params(self, params, **kwargs):
        if 'detector' not in params:
            print('detector name not parsed from metadata and not configured')
            raise KeyError('detector name not parsed from metadata and not configured')
        if self.diff_obj.detectordist_mne not in params:
            print('detdist not parsed from metadata and not configured')
            raise KeyError('detdist not parsed from metadata and not configured')
        if 'scanmot' not in params:
            print('scanmot not parsed from metadata and not configured')
            raise KeyError('scanmot not parsed from metadata and not configured')
        if 'energy' not in params:
            print('energy not parsed from metadata and not configured')
            raise KeyError('energy not parsed from metadata and not configured')
        if 'scanmot_posns' not in params:
            print('scanmot_posns not parsed from metadata')
        for ax in self.diff_obj.sampleaxes_mne:
            if ax != params['scanmot']:
                if ax not in params:
                    print(f'{ax} not parsed from metadata and not configured')
                    raise KeyError(f'{ax} not parsed from metadata and not configured')
        for ax in self.diff_obj.detectoraxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from metadata and not configured')
                raise KeyError(f'{ax} not parsed from metadata and not configured')


    def get_q2(self, scan, slices, roi):
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
        params.update(self.conf_params['config_instr'])
        # exception is raised if missing parameter
        self.check_params(params)
        params = self.convert_units(params)
        energy = params['energy']
        enfix = 1
        if m.floor(m.log10(energy)) < 3:
            enfix = 1000
        energy = energy * enfix  # x-ray energy in eV
        params['energy'] = energy

        scanmot = params['scanmot'].strip()

        if scanmot == 'en':
            raise ValueError('energy scan currently not supported')
        #     scanen = np.array((energy, energy + params['scanmot_del'] * enfix))
        else:
            scanen = np.array((energy,))

        # define scan_mot array for the slices
        scanmot_posns = params['scanmot_posns']
        if slices == 'all':
            scanmot_arr = np.array(scanmot_posns)
        else:
            scanmot_arr = np.array([scanmot_posns[slice] for slice in slices])

        det = self.det_obj
        diff = self.diff_obj

        args = []
        for sa in diff.sampleaxes_mne:
            if sa == params['scanmot']:
                args.append(scanmot_arr)
            else:
                args.append(params[sa])
        for da in diff.detectoraxes_mne:
            args.append(params[da])

        qc = xuexp.QConversion(diff.sampleaxes, diff.detectoraxes, diff.incidentaxis, en=scanen)
        # This is line from code in xrautilities.
        # self._area_roi = kwargs.get("roi", [0, self._area_Nch1, 0, self._area_Nch2])
        # The parameters 0, 0, will be overridden by roi.
        qc.init_area(det.pixelorientation[0], det.pixelorientation[1],
                     det.get_beamzero()[0], det.get_beamzero()[1],
                     0, 0,  # the values are ignored if roi is given
                     distance=params[diff.detectordist_mne],
                     pwidth1=det.pixel[0], pwidth2=det.pixel[1],
                     roi=roi)

        # q2 will always be (3,N,detroi1,detroi3) (vec, scanarr, Npx, Npy)
        q2 = np.squeeze(np.array(qc.area(*args, deg=True)))
        return q2, qc, params


    def get_pixelQ(self, pixel, scan):
        """
        Gets the Q value for a given pixel and slice in scan.

        :param pixel: tuple, (px, py) pixel coordinates
        :param scan: int, scan number
        :return: tuple, (qx, qy, qz) in inverse nm
        """
        # realpixelpos needs to correct for the relative pixel position in the roi.
        realpix = self.det_obj.get_realpixelpos(pixel)
        # xrayuntilties needs (start, end, start, end) so convert to that.
        roi = [realpix[0], realpix[0] + 1, realpix[1], realpix[1] + 1]
        slices = [pixel[2]]  # q2 vector for slice with max intensity
        q2, qc, params = self.get_q2(scan, slices, roi)

        # get the scan motor position corresponding to pixelQ
        params[params['scanmot']] = params['scanmot_posns'][pixel[2]]
        # transform to lab coords from sample reference frame
        q3 = qc.transformSample2Lab(q2, *[params[x] for x in self.diff_obj.sampleaxes_mne]) * 10.0  # convert to inverse nm.
        return q3


    def get_RSM(self, scan):
        det_roi = self.det_obj.get_det_roi()
        slices = 'all'  # q2 vector for all slices

        q2, qc, params = self.get_q2(scan, slices, det_roi)

        # TODO it expects single value for all sampleaxes motors, but scan motor will have many positions
        # for now set the scanmotor position to one in the middle
        middle_slice = params['scanmot_posns'].shape[0] // 2
        params[params['scanmot']] = params['scanmot_posns'][middle_slice]
        # transform to lab coords from sample reference frame
        q3 = qc.transformSample2Lab(q2.transpose(1, 2, 3, 0),
                                    *[params[x] for x in self.diff_obj.sampleaxes_mne]) * 10.0  # convert to inverse nm.

        return q3.transpose(1, 2, 0,
                            3)  # in order to match tiff in paraview.  Since paraview does not transpose on read the way we do.


    def get_geometry(self, max_ind, scan, conf_params, **kwargs):
        """
        Calculates geometry based on diffractometer and detector attributes and experiment parameters for given scan.

        Typically, the metadata such as detector axes, sample axes, camera distance, energy are parsed in a method
        specific to the beamline. The parsed values can be overridden by configuration.

        :param shape: tuple, shape of array
        :param scan: scan the geometry is calculated for
        :param conf_params: configuration parameters
        :return: tuple, geometry information
        """
        diff = self.diff_obj
        if 'config_data' in conf_params:
            binning = conf_params['config_data'].get('binning', [1,1,1])
        else:
            binning = [1,1,1]

        roi = [max_ind[0] - 1, max_ind[0] + 1,
               max_ind[1] - 1, max_ind[1] + 1]

        slices = [max_ind[2], max_ind[2] + 1]

        q2, qc, params = self.get_q2(scan, slices, roi)

        Astar = (q2[:, 0, 1, 0] - q2[:, 0, 0, 0]) * binning[0]
        Bstar = (q2[:, 0, 0, 1] - q2[:, 0, 0, 0]) * binning[1]
        Cstar = (q2[:, 1, 0, 0] - q2[:, 0, 0, 0]) * binning[2]

        xtal = kwargs.get('xtal', False)
        if xtal:
            Trecip_cryst = np.zeros(9)
            Trecip_cryst.shape = (3, 3)
            Trecip_cryst[:, 0] = Astar * 10
            Trecip_cryst[:, 1] = Bstar * 10
            Trecip_cryst[:, 2] = Cstar * 10
            return Trecip_cryst, None

        # get the scan motor position corresponding to pixelQ
        params[params['scanmot']] = params['scanmot_posns'][slices[0]]
        # transform to lab coords from sample reference frame
        Astar = qc.transformSample2Lab(Astar, *[params[x] for x in diff.sampleaxes_mne]) * 10.0  # convert to inverse nm.
        Bstar = qc.transformSample2Lab(Bstar, *[params[x] for x in diff.sampleaxes_mne]) * 10.0
        Cstar = qc.transformSample2Lab(Cstar, *[params[x] for x in diff.sampleaxes_mne]) * 10.0

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
        kf = qc.getDetectorPos(*[params[x] for x in diff.detectoraxes_mne],
                               deg=True)  # return in meters.  Not K as docs say.
        kf_hat = kf / np.linalg.norm(kf)
        ki = diff.incidentaxis
        ki_hat = ki / np.linalg.norm(ki)
        ki = 2 * np.pi / wl * ki_hat
        kf = 2 * np.pi / wl * kf_hat
        myq = kf - ki

        return (Trecip, Tdir, myq, ki, kf)


    def get_geometry_no_beamline(self, scan, config_params, **kwargs):
        """
        Calculates geometry based on diffractometer and detector attributes and experiment parameters for given scan.

        Typically, the metadata such as detector axes, sample axes, camera distance, energy are parsed in a method
        specific to the beamline. For no beamline the parameters are obtain from configuration.

        :param scan: scan the geometry is calculated for
        :param config_params: configuration parameters
        :return: tuple, geometry information
        """
        # check if all required parameters are in config_instr in config_params dict
        # if missing, the exception will stop processing
        params = config_params['config_instr']
        self.check_params(params)
        # check the scanmot parameter, if it's float or array
        scanmot = params['scanmot'].strip()
        scanmot_pos = params[scanmot]
        if isinstance(scanmot_pos, float):
            # need the scanmot_del (step) parameter, because only one position was given
            if 'scanmot_del' not in params:
                raise AttributeError('scanmot_del parameter is missing')
            else:
                scanmot_pos = [scanmot_pos, scanmot_pos + params['scanmot_del']]
        else:
            if isinstance(scanmot_pos, np.ndarray):
                scanmot_pos = scanmot_pos.tolist()
        # it should be converted list in any case
        if len(scanmot_pos) > 2:
            # get the middle position and the next
            scanmot_pos = [scanmot_pos[len(scanmot_pos) // 2], scanmot_pos[len(scanmot_pos) // 2 + 1]]
        scanmot_arr = np.array(scanmot_pos)

        if 'config_data' in config_params:
            binning = config_params['config_data'].get('binning', [1,1,1])
        else:
            binning = [1,1,1]

        energy = params['energy']
        enfix = 1
        if m.floor(m.log10(energy)) < 3:
            enfix = 1000
        energy = energy * enfix  # x-ray energy in eV
        params['energy'] = energy

        if scanmot == 'en':
            raise ValueError('energy scan currently not supported')
        #     scanen = np.array((energy, energy + params['scanmot_del'] * enfix))
        else:
            scanen = np.array((energy,))

        det = self.det_obj
        diff = self.diff_obj

        args = []
        for sa in diff.sampleaxes_mne:
            if sa == scanmot:
                args.append(scanmot_arr)
            else:
                args.append(params[sa])
        for da in diff.detectoraxes_mne:
            args.append(params[da])

        qc = xuexp.QConversion(diff.sampleaxes, diff.detectoraxes, diff.incidentaxis, en=scanen)

        # The roi should be position of max intensity in raw data array. Since it is no beamline
        # case, let choose arbitrary the beamzero.
        roi = [det.get_beamzero()[0] - 1, det.get_beamzero()[0] + 1,
               det.get_beamzero()[1] - 1, det.get_beamzero()[1] + 1]

        qc.init_area(det.pixelorientation[0], det.pixelorientation[1],
                     det.get_beamzero()[0], det.get_beamzero()[1],
                     0, 0,  # the values are ignored if roi is given
                     distance=params[diff.detectordist_mne],
                     pwidth1=det.pixel[0], pwidth2=det.pixel[1],
                     roi=roi)

        # q2 will always be (3,N,detroi1,detroi3) (vec, scanarr, Npx, Npy)
        q2 = np.squeeze(np.array(qc.area(*args, deg=True)))

        Astar = (q2[:, 0, 1, 0] - q2[:, 0, 0, 0]) * binning[0]
        Bstar = (q2[:, 0, 0, 1] - q2[:, 0, 0, 0]) * binning[1]
        Cstar = (q2[:, 1, 0, 0] - q2[:, 0, 0, 0]) * binning[2]

        xtal = kwargs.get('xtal', False)
        if xtal:
            Trecip_cryst = np.zeros(9)
            Trecip_cryst.shape = (3, 3)
            Trecip_cryst[:, 0] = Astar * 10
            Trecip_cryst[:, 1] = Bstar * 10
            Trecip_cryst[:, 2] = Cstar * 10
            return Trecip_cryst, None

        params[scanmot] = scanmot_pos[0]
        # transform to lab coords from sample reference frame
        Astar = qc.transformSample2Lab(Astar, *[params[x] for x in diff.sampleaxes_mne]) * 10.0  # convert to inverse nm.
        Bstar = qc.transformSample2Lab(Bstar, *[params[x] for x in diff.sampleaxes_mne]) * 10.0
        Cstar = qc.transformSample2Lab(Cstar, *[params[x] for x in diff.sampleaxes_mne]) * 10.0

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
        kf = qc.getDetectorPos(*[params[x] for x in diff.detectoraxes_mne],
                               deg=True)  # return in meters.  Not K as docs say.
        kf_hat = kf / np.linalg.norm(kf)
        ki = diff.incidentaxis
        ki_hat = ki / np.linalg.norm(ki)
        ki = 2 * np.pi / wl * ki_hat
        kf = 2 * np.pi / wl * kf_hat
        myq = kf - ki

        return (Trecip, Tdir, myq, ki, kf)
