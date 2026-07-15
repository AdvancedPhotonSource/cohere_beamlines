# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
import h5py
from cohere_beamlines.aps_28idb.diffractometers import Diffractometer
import cohere_beamlines.aps_28idb.detectors as det
from cohere_beamlines.common.instr import Instrument
from xrayutilities.io import spec


class Instrument_aps_28idb(Instrument):
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
        super(Instrument_aps_28idb, self).__init__(det_obj, diff_obj, conf_params)


    def convert_units(self, params):
        """
        Converts detectoraxes values from mm to m. The values are stored in params dict.
        :return:
        """
        params['detdist'] = params['detdist'] / 1000
        return params


    def parse_metadata(self, scan, **kwargs):
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
        dict with metadata
        """
        spec_dict = {}
        if 'specfile' in kwargs:
            specfile = kwargs['specfile']
        else:
            specfile = self.conf_params['config_instr'].get('specfile', None)
        if specfile is None or scan is None:
            return spec_dict

        # Scan numbers start at one but the list is 0 indexed
        try:
            sf = spec.SPECFile(specfile)
            ss = sf[scan - 1]
        except Exception as ex:
            print(str(ex))
            print('Could not parse ' + specfile)
            return spec_dict

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
            spec_dict['detdist'] = ss.init_motor_pos[motname]
        except:
            pass

        try:
            spec_dict['scanmot_posns'] = spec.getspec_scan(sf, scan, motmne_name_dict[spec_dict['scanmot']])[0]
        except Exception as ex:
            print(str(ex))

        try:
            spec_dict['energy'] = ss.init_motor_pos['INIT_MOPO_Energy']
        except:
            pass

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
        return self.det_obj.files4scans(self.scan_ranges)


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

    instr = Instrument_aps_28idb(det_obj, diff_obj, configs)
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