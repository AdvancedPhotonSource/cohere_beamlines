# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

from cohere_beamlines.aps_1ide.diffractometers import Diffractometer
from cohere_beamlines.common.instr import Instrument
import cohere_beamlines.aps_1ide.detectors as det
from xrayutilities.io import spec


class Instrument_aps_1ide(Instrument):
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
        super(Instrument_aps_1ide, self).__init__(det_obj, diff_obj, conf_params)


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


    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """

        params[self.diff_obj.detectordist_mne] = params[self.diff_obj.detectordist_mne] / 1000.0  # convert to meters
        params['vff_r'] = params['vff_r'] / 1000 + params['vff_r_offset']
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
        dict with metadata
        """
        spec_dict = {}
        if 'specfile' in kwargs:
            specfile = kwargs['specfile']
        else:
            specfile = self.conf_params['config_instr'].get('specfile', None)
        if specfile is None:
            # return empty dir
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
                print("failed from spec", mot_mne, mot_name)

        try:
            motname = "INIT_MOPO_{m}".format(m=self.diff_obj.detectordist_name)
            spec_dict['detdist'] = ss.init_motor_pos[motname]
        except:
            pass

        try:
            spec_dict['scanmot_posns'] = spec.getspec_scan(sf, scan, motmne_name_dict[spec_dict['scanmot']])[0]
        except Exception as ex:
            print(str(ex))

        try:
            spec_dict['detector'] = str(ss.getheader_element('UIMDET'))
            if spec_dict['detector'].endswith(':'):
                spec_dict['detector'] = spec_dict['detector'][:-1]
        except Exception as ex:
            print(str(ex))

        return spec_dict


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
    det_obj = None
    diff_obj = Diffractometer()
    main_config_params = configs['config']

    det_name = configs['config_instr'].get('detector', None)
    if det_name is None:
        raise ValueError('detector name not configured and could not be parsed')

    # set detector parameters to configured parameters in config_instr and processing
    # parameters from config_prep
    det_params = configs['config_instr']
    if 'config_prep' in  configs:
        det_params.update(configs['config_prep'])

    need_det = kwargs.get('need_det', False)
    if need_det:
        # check only if detector is created for reading data
        # check for parameters, it will raise exception if failed
        det.check_mandatory_params(det_name, det_params)
    det_obj = det.create_detector(det_name, det_params)

    instr = Instrument_aps_1ide(det_obj, diff_obj, configs)
    # set scan ranges in instrument class
    scan_ranges = None
    scan = main_config_params.get('scan', None)
    if scan is not None:
        # 'scan' is configured as string. It can be a single scan, range, or combination separated by comma.
        # Parse the scan into list of scan ranges, defined by starting scan, and ending scan, inclusive.
        # The single scan has range defined as the same starting and ending scan.
        scan_ranges = []
        scan_units = [u for u in scan.replace(' ','').split(',')]
        for u in scan_units:
            if '-' in u:
                r = u.split('-')
                scan_ranges.append([int(r[0]), int(r[1])])
            else:
                scan_ranges.append([int(u), int(u)])
    instr.scan_ranges = scan_ranges

    return instr
