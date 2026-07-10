from cohere_beamlines.simple.diffractometers import Diffractometer
from cohere_beamlines.common.instr import Instrument
import cohere_beamlines.simple.detectors as det


class Instrument_simple(Instrument):
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
        super(Instrument_simple, self).__init__(det_obj, diff_obj, conf_params)


    def datainfo4scans(self):
        """
        Finds info allowing to read data that correspond to given scans or scan ranges.
        The info can be directories where the data related to scans is stored or nodes in hd5 file
        that contain the data, or other info specific to a beamline.

        :param scans : list
            list of sub-lists defining scan ranges, ordered. For single scan a range has the same scan as beginning and end.
            one scan example:
            scans : [[2834, 2834]]
            returns : [[(2834, f'{path}/data_S2834)]]

            separate ranges example:
            scans: [[2825, 2831], [2834, 2834], [2840, 2846]]
            returns: [[(2825, f'{path}/data_S2825'), (2828, f'{path}/data_S2828'), (2831, f'{path}/data_S2831')],
             [(2834, f'{path}/data_S2834)],
             [(2840, f'{path}/data_S2840'), (2843, f'{path}/data_S2843'), (2846, f'{path}/data_S2846')]]

        :return:
        list of sub-lists, each sublist containing tuples with the input scans and corresponding data info
         within scan ranges.
        """
        # The detector function is typically renamed to reflect the info.
        # if the info is directory, the function name would be dirs4scans
        # if the info is hdf5 file node, the function name would be nodes4scans
        if self.det_obj is None:
            print('detector object not created, check config parameters')
        return self.det_obj.datainfo4scans(self.scan_ranges)


    def get_scan_array(self, scan):
        """
        Gets the data for the scan. The data is corrected for the detector.

        :param scan_info: info allowing detector to retrieve data for a scan
        :return: corrected data array
        """
        return self.det_obj.get_scan_array(scan)


    def parse_metadata(self, scan, **kwargs):
        """
        Returns empty dict, as for simple beamline there is no metadata, all params are configured.

        Parameters
        ----------
        scan : int
            scan number to use to recover the saved measurements

        Returns
        -------
        metadata
        """
        return {}


def create_instr(configs, **kwargs):
    """
    Build factory for the Instrument class.

    :param : dict
        the parameters typically parsed from config file

    Returns
    -------
    Object or None
        Instrument object or None
    """
    diff_obj = Diffractometer()
    instr_config_params = configs['config_instr']
    det_name = instr_config_params.get('detector', None)
    if det_name is None:
        raise ValueError('detector name not configured in config_instr')

    det_params = instr_config_params
    if 'config_prep' in configs:
        det_params.update(configs['config_prep'])
    det_obj = det.create_detector(det_name, det_params)

    instr = Instrument_simple(det_obj, diff_obj, configs)
    main_conf = configs['config']
    if 'scan' in main_conf:
        instr.scan_ranges = [[int(main_conf['scan']), int(main_conf['scan'])]]

    return instr
