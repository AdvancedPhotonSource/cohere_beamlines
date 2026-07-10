# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from cohere_beamlines.aps_7idd.diffractometers import Diffractometer
import cohere_beamlines.aps_7idd.detectors as det
from xrayutilities.io import spec
from cohere_beamlines.common.instr import Instrument


def parse_detector(specfile, scan, det=None):
    """
    Returns detector name and detector area parsed from spec file for given scan.

    Parameters
    ----------
    specfile : str
        spec file name

    scan : int
        scan number to use to recover the saved measurements

    Returns
    -------
    dict
        dictionary of parameters; name : value
    """
    params = {}
    # Scan numbers start at one but the list is 0 indexed, so we subtract 1
    if det is None:
        try:
            ss = spec.SPECFile(specfile)[scan - 1]
        except Exception as ex:
            print(str(ex))
            print('Could not parse ' + specfile)
            return params

        try:
            params['detector'] = str(ss.getheader_element('UIMDET'))
            if params['detector'].endswith(':'):
                params['detector'] = params['detector'][:-1]
        except Exception as ex:
            print(str(ex))

    try:
        params['roi'] = [int(n) for n in ss.getheader_element('UIMR5').split()]
    except Exception as ex:
        pass
        # print (str(ex))

    return params


class Instrument_aps_7idd(Instrument):
    """
      This class encapsulates istruments: diffractometer and detector used for that experiment.
      It provides interface to get the classes encapsulating the diffractometer and detector.
    """

    def __init__(self, det_obj, diff_obj, conf_params):
        """
        Constructor

        :param det_obj: detector object
        :param diff_obj: diffractometer object
        """
        super(Instrument_aps_7idd, self).__init__(det_obj, diff_obj, conf_params)


    def convert_units(self, params):
        """
        Converts detector axes values from mm to m. The values are stored in params dict.
        :return:
        """

        params[self.diff_obj.detectordist_mne] = params[self.diff_obj.detectordist_mne] / 1000.0  # convert to meters
        return params


    def parse_metadata(self, scan, **kwargs):
        """
        Reads parameters from spec file for given scan.

        Parameters
        ----------
        scan : int
            scan number to use to recover the saved measurements

        Returns
        -------
        dict with delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector_name, energy
        """
        if 'specfile' in kwargs:
            specfile = kwargs['specfile']
        else:
            params = self.conf_params['config_instr']
            specfile = params.get('specfile', None)

        spec_dict = {}
        if specfile is None or scan is None:
            return spec_dict

        # Scan numbers start at one but the list is 0 indexed
        try:
            sf = spec.SPECFile(specfile)
            ss = sf[scan - 1]
        except Exception as ex:
            print(str(ex))
            print('Could not parse ' + specfile)
            return None

        try:
            command = ss.command.split()
            spec_dict['scanmot'] = command[1]
        except:
            pass

        motmne_name_dict = {**dict(zip(self.diff_obj.sampleaxes_mne, self.diff_obj.sampleaxes_name)),
                            **dict(zip(self.diff_obj.detectoraxes_mne, self.diff_obj.detectoraxes_name))}

        for mot_mne, mot_name in motmne_name_dict.items():
            try:
                motname = "INIT_MOPO_{m}".format(m=mot_name)
                spec_dict[mot_mne] = ss.init_motor_pos[motname]
            except:
                pass
        try:
            motname = "INIT_MOPO_{m}".format(m=self.diff_obj.detectordist_name)
            spec_dict[self.diff_obj.detectordist_mne] = ss.init_motor_pos[motname]
        except:
            pass

        try:
            spec_dict['energy'] = ss.init_motor_pos['INIT_MOPO_Energy']
        except:
            pass

        try:
            spec_dict['detector'] = str(ss.getheader_element('UIMDET'))
            if spec_dict['detector'].endswith(':'):
                spec_dict['detector'] = spec_dict['detector'][:-1]
        except Exception as ex:
            print(str(ex))

        try:
            spec_dict['scanmot_posns'] = spec.getspec_scan(sf, scan, motmne_name_dict[spec_dict['scanmot']])[0]
        except Exception as ex:
            print(str(ex))

        try:
            roi = ss.getheader_element('UIMR5')
            if type(roi) == list:
                if len(roi) > 0:
                    roi = roi[0]
                    spec_dict['roi'] = [int(n) for n in roi.split()]
        except Exception as ex:
            print(str(ex))

        return spec_dict


    def datainfo4scans(self):
        """
        Finds existing sub-directories in data_dir that correspond to given scans and scan ranges.
        Parameters
        ----------
        Returns
        -------
        list
        """
        return self.det_obj.dirs4scans(self.scan_ranges)


    def get_scan_array(self, scan_dir):
        return self.det_obj.get_scan_array(scan_dir)


def create_instr(configs, **kwargs):
    """
    Build factory for the Instrument class.

    Parameters
    ----------
    configs : dict
        the parameters parsed from config file

    Returns
    -------
    (str, Object)
        error msg, Instrument object or None
    """
    diff_obj = Diffractometer()
    scan_ranges = None
    det_params = {}
    main_config_params = configs['config']
    instr_config_params = configs['config_instr']

    # parse scans to be saved in instrument object
    scan = main_config_params.get('scan', None)
    if 'config_mp' in configs:
        scan = configs['config_mp'].get('scan', None)
    if scan is not None:
        # 'scan' is configured as string. It can be a single scan, range, or combination separated by comma.
        # Parse the scan into list of scan ranges, defined by starting scan, and ending scan, inclusive.
        # The single scan has range defined as the same starting and ending scan.
        scan_ranges = []
        scan_units = [u for u in scan.replace(' ', '').split(',')]
        for u in scan_units:
            if '-' in u:
                r = u.split('-')
                scan_ranges.append([int(r[0]), int(r[1])])
            else:
                scan_ranges.append([int(u), int(u)])

        # parse detector name from metadata
        if 'specfile' in instr_config_params and scan is not None:
            # detector name is parsed from specfile if one exists
            # Find the first scan to parse detector params.
            first_scan = scan_ranges[0][0]
            det_params = parse_detector(instr_config_params.get('specfile'), first_scan)

    det_params.update(instr_config_params)
    if 'config_prep' in configs:
        det_params.update(configs['config_prep'])

    # get detector name
    detector = det_params.get('detector', None)
    if detector is None:
        raise ValueError('detector name not configured and could not be parsed')

    need_det = kwargs.get('need_det', False)
    if need_det:
        # check only if detector is created for reading data
        # check for parameters, it will raise exception if failed
        det.check_mandatory_params(detector, det_params)

    det_obj = det.create_detector(detector, det_params)
    if det_obj is None:
        msg = f'failed create {detector} detector'
        raise ValueError(msg)

    instr = Instrument_aps_7idd(det_obj, diff_obj, configs)
    instr.scan_ranges = scan_ranges

    return instr