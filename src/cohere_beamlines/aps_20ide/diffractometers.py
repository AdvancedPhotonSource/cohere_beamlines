# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
import os
import numpy as np
import h5py
import math as m
import xrayutilities.experiment as xuexp
from xrayutilities.io import spec as spec
import xrayutilities.utilities_noconf as xutilnoconf
import cohere_beamlines.aps_20ide.detectors as det
import cohere_core.utilities as ut
from abc import ABC


class Diffractometer(ABC):
    """
    Abstract class representing diffractometer. It keeps fields related to the specific diffractometer represented by
    a subclass.

    diff_name : str
        diffractometer name
    """
    name = None

    def __init__(self, diff_name):
        """
        Constructor.

        Parameters
        ----------
        diff_name : str
            diffractometer name

        """
        self.name = diff_name


class Diffractometer_20ide(Diffractometer):
    """
    Subclass of Diffractometer. Encapsulates "20ide" diffractometer.
    """
    name = "20ide"
    sampleaxes=('y+')  #omega is postive up
    detectoraxes=('z+','ty','tx')
    incidentaxis = (0, 0, 1)
    #motors from spec file.
    sampleaxes_name = ('LabMotion',)
    sampleaxes_mne = ('samRy',)
    detectoraxes_name = ('VFF_ETA', 'VFF_R')
    detectoraxes_mne = ('VFF_ETA', 'VFF_R')
    detectordist_name = 'camdist'
    detectordist_mne = 'DetZ'

    
    def __init__(self, params):
        super(Diffractometer_20ide, self).__init__('20ide')
        self.data_dir = params.get('data_dir', None)
    
    def parse_h5(self, scan):
        """
        Reads parameters from h5 file for given scan.

        Parameters
        ----------
        h5file : str
            h5 file name

        scan : int
            scan number to use to recover the saved measurements

        diff : object
            diffractometer object

        Returns
        -------
        dict with delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector_name, energy
        """
        h5_dict = {}

        # find the file by scan number
        for scanfile in os.listdir(self.data_dir):
            scanfile_full = ut.join(self.data_dir, scanfile)
            if not os.path.isfile(scanfile_full) or not scanfile_full.endswith('.h5'):
                continue
            # chop off the ".h5" and get the scan number
            try:
                read_scan = int(scanfile[:-3].split('_')[-1])
            except:
                continue
            if read_scan == scan:
                h5file = scanfile_full
                break

        h5f = h5py.File(h5file)
        scanmot = self.sampleaxes_mne[0]
        h5_dict['scanmot'] = scanmot
        try:
            h5_dict[scanmot] = h5f[f'SMS/D/HR/{scanmot}'][:]
        except:
            pass
        for mot_mne in self.detectoraxes_mne:
            try:
                h5_dict[mot_mne] = h5f[f'instrument/DMS/{mot_mne}'][0]
            except:
                pass
        try:
            h5_dict[self.detectordist_mne] = h5f[f'instrument/DMS/{self.detectordist_mne}'][0]
        except:
            pass
        try:
            h5_dict['energy'] = h5f['HEM/Energy'][0]
        except Exception as ex:
            # print(f"{__name__}: {ex}")
            pass

        h5f.close()
        return h5_dict

    def check_params(self, params):
        if 'detector' not in params:
            print('detector name not parsed from h5 file and not configured')
            raise KeyError('detector name not parsed from h5 file and not configured')
        if 'DetZ' not in params:
            print('DetZ not parsed from h5 file and not configured')
            raise KeyError('DetZ not parsed from sh5 file and not configured')
        if 'scanmot' not in params:
            print('scanmot not parsed from spec file and not configured')
            raise KeyError('scanmot not parsed from spec file and not configured')
        if 'energy' not in params:
            print('energy not parsed from h5 file and not configured')
            raise KeyError('energy not parsed from h5 file and not configured')
        for ax in self.sampleaxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from h5 file and not configured')
                raise KeyError (f'{ax} not parsed from h5 file and not configured')
        for ax in self.detectoraxes_mne:
            if ax not in params:
                print(f'{ax} not parsed from h5 file and not configured')
                raise KeyError (f'{ax} not parsed from h5 file and not configured')


    def get_geometry(self, shape, scan, conf_params):
        """
        Calculates geometry based on diffractometer and detector attributes and experiment parameters.

        :param shape: tuple, shape of array
        :param scan: scan the geometry is calculated for
        :param conf_params: reflect configuration
        :return: tuple
            (Trecip, Tdir)
        """
        params = {}
        # parse h5 file for metadata
        params.update(self.parse_h5(scan))
        # override with config params
        params.update(conf_params)
        self.check_params(params)

        binning = params.get('binning', [1, 1, 1])
        pixel = det.get_pixel(params['detector'])
        px = pixel[0] * binning[0]
        py = pixel[1] * binning[1]

        DetZ = params['DetZ'] #/ 1000.0  # convert to meters
        scanmot = params['scanmot']
        enfix = 1
        # if energy is given in kev convert to ev for xrayutilities
        energy = params['energy']
        if m.floor(m.log10(energy)) < 3:
            enfix = 1000
        energy = energy * enfix  # x-ray energy in eV
        scanen = np.array((energy,))
        qc = xuexp.QConversion(self.sampleaxes, self.detectoraxes, self.incidentaxis, en=scanen)

        # compute for 4pixel (2x2) detector
        pixelorientation = det.get_pixel_orientation(params['detector'])
        qc.init_area(pixelorientation[0], pixelorientation[1], shape[0], shape[1], 2, 2,
                     distance=DetZ, pwidth1=px, pwidth2=py)

        if scanmot in self.sampleaxes_mne:  # based on scanmot args are made for qc.area
            args = []
            for sampleax in self.sampleaxes_mne:
                if scanmot == sampleax:
                    args.append(params[scanmot] * binning[2])
                else:
                    args.append(params[sampleax])
            args.append(params['VFF_ETA'])
            args.append(params['VFF_R'] / 1000) # + params['vff_r_offset'])
            # append 0 for vff_eta_offset
            args.append(0)
            q2 = np.array(qc.area(*args, deg=True))

        # I think q2 will always be (3,2,2,2) (vec, scanarr, px, py)
        Astar = q2[:, 0, 1, 0] - q2[:, 0, 0, 0]
        Bstar = q2[:, 0, 0, 1] - q2[:, 0, 0, 0]
        Cstar = q2[:, 1, 0, 0] - q2[:, 0, 0, 0]

        # transform to lab coords from sample reference frame
        scanmot_start = params[scanmot][0]
        Astar = qc.transformSample2Lab(Astar, scanmot_start) * 10.0  # convert to inverse nm.
        Bstar = qc.transformSample2Lab(Bstar, scanmot_start) * 10.0
        Cstar = qc.transformSample2Lab(Cstar, scanmot_start) * 10.0

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

        # wl = xutilnoconf.en2lam(energy)
        # args = []
        # for axis in self.detectoraxes_mne:
        #     args.append(params[axis])
        # kf = qc.getDetectorPos(*args, deg=True)  # return in meters.  Not K as docs say.
        # kf_hat = kf / np.linalg.norm(kf)
        # ki = self.incidentaxis
        # ki_hat = ki / np.linalg.norm(ki)
        # ki = 2 * np.pi / wl * ki_hat
        # kf = 2 * np.pi / wl * kf_hat
        # myq = kf - ki
        #
        # return (Trecip, Tdir, myq, ki, kf)

        return (Trecip, Tdir, None, None, None)

def create_diffractometer(diff_name, params):
    for diff in Diffractometer.__subclasses__():
        if diff.name == diff_name:
            return diff(params)

    msg = f'diffractometor {diff_name} not defined'
    raise ValueError(msg)
