import numpy as np
from abc import ABC
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
    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """

        return params


    def check_params(self, params):
        if 'detector' not in params:
            print('detector name not parsed from spec file and not configured')
            raise KeyError('detector name not parsed from spec file and not configured')
        if self.detectordist_mne not in params:
            print('detdist not parsed from spec file and not configured')
            raise KeyError('detdist not parsed from spec file and not configured')
        if 'scanmot' not in params:
            print('scanmot not parsed from spec file and not configured')
            raise KeyError('scanmot not parsed from spec file and not configured')
        if 'energy' not in params:
            print('energy not parsed from spec file and not configured')
            raise KeyError('energy not parsed from spec file and not configured')
        if 'scanmot_del' not in params:
            print('scanmot_del not parsed from spec file and not configured')
            raise KeyError('scanmot_del not parsed from spec file and not configured')
        for ax in self.sampleaxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from spec file and not configured')
                raise KeyError (f'{ax} not parsed from spec file and not configured')
        for ax in self.detectoraxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from spec file and not configured')
                raise KeyError (f'{ax} not parsed from spec file and not configured')


    def get_geometry(self, shape, scan, conf_params, det, **kwargs):
        """
        Calculates geometry based on diffractometer and detector attributes and experiment parameters for given scan.

        Typically, the metadata such as detector axes, sample axes, camera distance, energy are parsed in a manner
        specific to the beamline. The parsed values can be overridden by configuration.

        :param shape: tuple, shape of array
        :param scan: scan the geometry is calculated for
        :param conf_params: configuration parameters
        :return: tuple, geometry information
        """
        params = {}
        # parse spec file for metadata
        params.update(self.parse_metadata(scan))
        # override with config params
        params.update(conf_params)
        # exception is raised if missing parameter
        self.check_params(params)
        params = self.convert_units(params)

        binning = params.get('binning', [1, 1, 1])
        pixel = det.get_pixel(params['detector'])
        px = pixel[0] * binning[0]
        py = pixel[1] * binning[1]

        scanmot = params['scanmot'].strip()
        enfix = 1
        # if energy is given in kev convert to ev for xrayutilities
        energy = params['energy']
        if m.floor(m.log10(energy)) < 3:
            enfix = 1000
        energy = energy * enfix  # x-ray energy in eV

        if scanmot == 'en':
            scanen = np.array((energy, energy + params['scanmot_del'] * enfix))
        else:
            scanen = np.array((energy,))
        qc = xuexp.QConversion(self.sampleaxes, self.detectoraxes, self.incidentaxis, en=scanen)

        # compute for 4pixel (2x2) detector
        pixelorientation = det.get_pixel_orientation(params['detector'])
        qc.init_area(pixelorientation[0], pixelorientation[1], shape[0], shape[1], 2, 2,
                     distance=params[self.detectordist_mne], pwidth1=px, pwidth2=py)

        # q2 will always be (3,2,2,2) (vec, scanarr, px, py)
        args = []
        for sa in self.sampleaxes_mne:
            if scanmot == sa:
                scanstart = params[scanmot]
                args.append(np.array((scanstart, scanstart + params['scanmot_del'] * binning[2])))
            else:
                args.append(params[sa])
        for da in self.detectoraxes_mne:
            args.append(params[da])

        q2 = np.array(qc.area(*args, deg=True))

        # I think q2 will always be (3,2,2,2) (vec, scanarr, px, py)
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

        wl = xutilnoconf.en2lam(energy)
        kf = qc.getDetectorPos(*[params[x] for x in self.detectoraxes_mne], deg=True) # return in meters.  Not K as docs say.
        kf_hat = kf / np.linalg.norm(kf)
        ki = self.incidentaxis
        ki_hat = ki / np.linalg.norm(ki)
        ki = 2 * np.pi / wl * ki_hat
        kf = 2 * np.pi / wl * kf_hat
        myq = kf - ki

        return (Trecip, Tdir, myq, ki, kf)
