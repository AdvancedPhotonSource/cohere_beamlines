# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import ast
import cohere_core.utilities as ut
import cohere_beamlines.aps_34idc.beam_verifier as ver
import cohere_beamlines.aps_34idc.instrument as instr
import cohere_beamlines.aps_34idc.diffractometers as diff


def msg_window(text):
    """
    Shows message with requested information (text)).
    Parameters
    ----------
    text : str
        string that will show on the screen
    Returns
    -------
    noting
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setText(text)
    msg.setWindowTitle("Info")
    msg.exec()


def select_file(start_dir):
    """
    Shows dialog interface allowing user to select file from file system.
    Parameters
    ----------
    start_dir : str
        directory where to start selecting the file
    Returns
    -------
    str
        name of selected file or None
    """
    start_dir = start_dir.replace(os.sep, '/')
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return str(dialog.selectedFiles()[0]).replace(os.sep, '/')
    else:
        return None


def select_dir(start_dir):
    """
    Shows dialog interface allowing user to select directory from file system.
    Parameters
    ----------
    start_dir : str
        directory where to start selecting
    Returns
    -------
    str
        name of selected directory or None
    """
    start_dir = start_dir.replace(os.sep, '/')
    dialog = QFileDialog(None, 'select dir', start_dir)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setSidebarUrls([QUrl.fromLocalFile(start_dir)])
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return str(dialog.selectedFiles()[0]).replace(os.sep, '/')
    else:
        return None


def set_overriden(item):
    """
    Helper function that will set the text color to black.
    Parameters
    ----------
    item : widget
    Returns
    -------
    nothing
    """
    item.setStyleSheet('color: black')


class SubInstrTab():
    def init(self, instr_tab, main_window):
        """
        Creates and initializes the 'Instrument' tab.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        self.main_window = main_window
        self.instr_tab = instr_tab

        self.spec_widget = QWidget()
        spec_layout = QFormLayout()
        self.spec_widget.setLayout(spec_layout)
        self.energy = QLineEdit()
        spec_layout.addRow("energy", self.energy)
        self.delta = QLineEdit()
        spec_layout.addRow("delta (deg)", self.delta)
        self.gamma = QLineEdit()
        spec_layout.addRow("gamma (deg)", self.gamma)
        self.detdist = QLineEdit()
        spec_layout.addRow("detdist (mm)", self.detdist)
        self.th = QLineEdit()
        spec_layout.addRow("th (deg)", self.th)
        self.chi = QLineEdit()
        spec_layout.addRow("chi (deg)", self.chi)
        self.phi = QLineEdit()
        spec_layout.addRow("phi (deg)", self.phi)
        self.scanmot = QLineEdit()
        spec_layout.addRow("scan motor", self.scanmot)
        self.detector = QLineEdit()
        spec_layout.addRow("detector", self.detector)

        self.energy.textChanged.connect(lambda: set_overriden(self.energy))
        self.delta.textChanged.connect(lambda: set_overriden(self.delta))
        self.gamma.textChanged.connect(lambda: set_overriden(self.gamma))
        self.detdist.textChanged.connect(lambda: set_overriden(self.detdist))
        self.th.textChanged.connect(lambda: set_overriden(self.th))
        self.chi.textChanged.connect(lambda: set_overriden(self.chi))
        self.phi.textChanged.connect(lambda: set_overriden(self.phi))
        self.scanmot.textChanged.connect(lambda: set_overriden(self.scanmot))
        self.detector.textChanged.connect(lambda: set_overriden(self.detector))


    def load_tab(self, conf_map):
        """
        It verifies given configuration file, reads the parameters, and fills out the window.
        Parameters
        ----------
        conf : dict
            configuration (config_instr)
        Returns
        -------
        nothing
        """
        self.parse_spec()

        # if parameters are configured, override the readings from spec file
        if 'energy' in conf_map:
            self.energy.setText(str(conf_map['energy']).replace(" ", ""))
            self.energy.setStyleSheet('color: black')
        if 'delta' in conf_map:
            self.delta.setText(str(conf_map['delta']).replace(" ", ""))
            self.delta.setStyleSheet('color: black')
        if 'gamma' in conf_map:
            self.gamma.setText(str(conf_map['gamma']).replace(" ", ""))
            self.gamma.setStyleSheet('color: black')
        if 'detdist' in conf_map:
            self.detdist.setText(str(conf_map['detdist']).replace(" ", ""))
            self.detdist.setStyleSheet('color: black')
        if 'th' in conf_map:
            self.th.setText(str(conf_map['th']).replace(" ", ""))
            self.th.setStyleSheet('color: black')
        if 'chi' in conf_map:
            self.chi.setText(str(conf_map['chi']).replace(" ", ""))
            self.chi.setStyleSheet('color: black')
        if 'phi' in conf_map:
            self.phi.setText(str(conf_map['phi']).replace(" ", ""))
            self.phi.setStyleSheet('color: black')
        if 'scanmot' in conf_map:
            self.scanmot.setText(str(conf_map['scanmot']).replace(" ", ""))
            self.scanmot.setStyleSheet('color: black')
        if 'detector' in conf_map:
            self.detector.setText(str(conf_map['detector']).replace(" ", ""))
            self.detector.setStyleSheet('color: black')


    def clear_conf(self):
        self.energy.setText('')
        self.delta.setText('')
        self.gamma.setText('')
        self.detdist.setText('')
        self.th.setText('')
        self.chi.setText('')
        self.phi.setText('')
        self.scanmot.setText('')
        self.detector.setText('')


    def get_instr_config(self):
        """
        It reads parameters related to instrument from the window into a dictionary.
        Parameters
        ----------
        none
        Returns
        -------
        conf_map : dict
            contains parameters read from window
        """
        conf_map = {}
        if len(self.energy.text()) > 0:
            conf_map['energy'] = ast.literal_eval(str(self.energy.text()))
        if len(self.delta.text()) > 0:
            conf_map['delta'] = ast.literal_eval(str(self.delta.text()))
        if len(self.gamma.text()) > 0:
            conf_map['gamma'] = ast.literal_eval(str(self.gamma.text()))
        if len(self.detdist.text()) > 0:
            conf_map['detdist'] = ast.literal_eval(str(self.detdist.text()))
        if len(self.th.text()) > 0:
            conf_map['th'] = ast.literal_eval(str(self.th.text()))
        if len(self.chi.text()) > 0:
            conf_map['chi'] = ast.literal_eval(str(self.chi.text()))
        if len(self.phi.text()) > 0:
            conf_map['phi'] = ast.literal_eval(str(self.phi.text()))
        if len(self.scanmot.text()) > 0:
            conf_map['scanmot'] = str(self.scanmot.text())
        if len(self.detector.text()) > 0:
            conf_map['detector'] = str(self.detector.text())

        return conf_map


    def parse_spec(self):
        """
        Calls utility function to parse spec file. Displas the parsed parameters in the window with blue text.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        if not self.main_window.loaded and not self.main_window.is_exp_set():
            return
        scan = str(self.main_window.scan_widget.text())
        if len(scan) == 0:
            msg_window ('cannot parse spec, scan not defined')
            return

        specfile = self.instr_tab.spec_file_button.text()
        if len(specfile) == 0:
            msg_window ('cannot parse spec, specfile not defined')
            return

        try:
            diff_obj = diff.Diffractometer()
        except Exception as e:
            msg_window (str(e))
            return

        first_scan = int(scan.split('-')[0].split(',')[0])
        instrument = instr.Instrument_aps_34idc(None, diff_obj, None)
        spec_dict = instrument.parse_metadata(first_scan, specfile=specfile)
        if spec_dict is None:
            return
        if 'energy' in spec_dict:
            self.energy.setText(str(spec_dict['energy']))
            self.energy.setStyleSheet('color: blue')
        if 'delta' in spec_dict:
            self.delta.setText(str(spec_dict['delta']))
            self.delta.setStyleSheet('color: blue')
        if 'gamma' in spec_dict:
            self.gamma.setText(str(spec_dict['gamma']))
            self.gamma.setStyleSheet('color: blue')
        if 'th' in spec_dict:
            self.th.setText(str(spec_dict['th']))
            self.th.setStyleSheet('color: blue')
        if 'chi' in spec_dict:
            self.chi.setText(str(spec_dict['chi']))
            self.chi.setStyleSheet('color: blue')
        if 'phi' in spec_dict:
            self.phi.setText(str(spec_dict['phi']))
            self.phi.setStyleSheet('color: blue')
        if 'detdist' in spec_dict:
            self.detdist.setText(str(spec_dict['detdist']))
            self.detdist.setStyleSheet('color: blue')
        if 'scanmot' in spec_dict:
            self.scanmot.setText(str(spec_dict['scanmot']))
            self.scanmot.setStyleSheet('color: blue')
        if 'detector' in spec_dict:
            self.detector.setText(str(spec_dict['detector']))
            self.detector.setStyleSheet('color: blue')

        if 'det_roi' in spec_dict:
            self.instr_tab.det_roi.setText(str(spec_dict['det_roi']))
            self.instr_tab.det_roi.setStyleSheet('color: blue')



class InstrTab(QWidget):
    def __init__(self, parent=None):
        """
        Constructor, initializes the tabs.
        """
        super(InstrTab, self).__init__(parent)
        self.name = 'Instrument'
        self.conf_name = 'config_instr'


    def toggle_config(self):
        if self.main_win.multipeak.isChecked() or self.main_win.separate_scans.isChecked() or self.main_win.separate_scan_ranges.isChecked():
            self.add_config = False
            self.extended.clear_conf()
            self.extended.spec_widget.hide()
        else:
            self.add_config = True
            self.extended.spec_widget.show()
            self.extended.parse_spec()
        if self.main_win.loaded:
            self.save_conf()


    def init(self, tabs, main_window):
        """
        Creates and initializes the 'Instrument' tab.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        self.tabs = tabs
        self.main_win = main_window
        self.extended = None
        if main_window.multipeak.isChecked() or main_window.separate_scans.isChecked() or main_window.separate_scan_ranges.isChecked():
            self.add_config = False
        else:
            self.add_config = True
        self.extended = SubInstrTab()
        self.extended.init(self, main_window)

        tab_layout = QVBoxLayout()
        gen_layout = QFormLayout()
        self.spec_file_button = QPushButton()
        gen_layout.addRow("spec file", self.spec_file_button)
        self.data_dir_button = QPushButton()
        gen_layout.addRow("data directory", self.data_dir_button)
        self.dark_file_button = QPushButton()
        gen_layout.addRow("darkfield file", self.dark_file_button)
        self.white_file_button = QPushButton()
        gen_layout.addRow("whitefield file", self.white_file_button)
        self.Imult = QLineEdit()
        gen_layout.addRow("Imult", self.Imult)
        self.det_roi = QLineEdit()
        gen_layout.addRow("detector area (det_roi)", self.det_roi)
        self.beam_zero = QLineEdit()
        gen_layout.addRow("beam zero position [x, y]", self.beam_zero)
        tab_layout.addLayout(gen_layout)
        tab_layout.addWidget(self.extended.spec_widget)
        if not self.add_config:
            self.extended.spec_widget.hide()
        cmd_layout = QHBoxLayout()
        self.set_instr_conf_from_button = QPushButton("Load instr conf from")
        self.set_instr_conf_from_button.setStyleSheet("background-color:rgb(205,178,102)")
        self.save_instr_conf = QPushButton('save config', self)
        self.save_instr_conf.setStyleSheet("background-color:rgb(175,208,156)")
        cmd_layout.addWidget(self.set_instr_conf_from_button)
        cmd_layout.addWidget(self.save_instr_conf)
        tab_layout.addLayout(cmd_layout)
        tab_layout.addStretch()
        self.setLayout(tab_layout)

        self.spec_file_button.clicked.connect(self.set_spec_file)
        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.dark_file_button.clicked.connect(self.set_dark_file)
        self.white_file_button.clicked.connect(self.set_white_file)
        self.det_roi.textChanged.connect(lambda: set_overriden(self.det_roi))
        self.save_instr_conf.clicked.connect(self.save_conf)
        self.set_instr_conf_from_button.clicked.connect(self.load_instr_conf)


    def run_tab(self):
        pass


    def load_tab(self, conf_map):
        """
        It verifies given configuration file, reads the parameters, and fills out the window.
        Parameters
        ----------
        conf : dict
            configuration (config_instr)
        Returns
        -------
        nothing
        """
        if 'specfile' in conf_map:
            specfile = conf_map['specfile']
            if os.path.isfile(specfile):
                self.spec_file_button.setStyleSheet("Text-align:left")
                self.spec_file_button.setText(specfile)
            else:
                msg_window(f'The specfile file {specfile} in config file does not exist')
        if 'data_dir' in conf_map:
            if os.path.isdir(conf_map['data_dir']):
                self.data_dir_button.setStyleSheet("Text-align:left")
                self.data_dir_button.setText(conf_map['data_dir'])
            else:
                msg_window(f'The data_dir directory in config_prep file {conf_map["data_dir"]} does not exist')
        else:
            self.data_dir_button.setText('')
        if 'darkfield_filename' in conf_map:
            if os.path.isfile(conf_map['darkfield_filename']):
                self.dark_file_button.setStyleSheet("Text-align:left")
                self.dark_file_button.setText(conf_map['darkfield_filename'])
            else:
                msg_window(f'The darkfield file {conf_map["darkfield_filename"]} in config_prep file does not exist')
                self.dark_file_button.setText('')
        else:
            self.dark_file_button.setText('')
        if 'whitefield_filename' in conf_map:
            if os.path.isfile(conf_map['whitefield_filename']):
                self.white_file_button.setStyleSheet("Text-align:left")
                self.white_file_button.setText(conf_map['whitefield_filename'])
            else:
                self.white_file_button.setText('')
                msg_window(f'The whitefield file {conf_map["whitefield_filename"]} in config_prep file does not exist')
        else:
            self.white_file_button.setText('')
        if 'Imult' in conf_map:
            self.Imult.setText(str(conf_map['Imult']).replace(" ", ""))
        if 'det_roi' in conf_map:
            self.det_roi.setText(str(conf_map['det_roi']).replace(" ", ""))
            self.det_roi.setStyleSheet('color: black')
        if 'beam_zero' in conf_map:
            self.beam_zero.setText(str(conf_map['beam_zero']).replace(" ", ""))
            self.beam_zero.setStyleSheet('color: black')

        if self.add_config:
            self.extended.load_tab(conf_map)


    def set_spec_file(self):
        """
        Calls selection dialog. The selected spec file is parsed.
        The specfile is saved in config.
        Parameters
        ----------
        none
        Returns
        -------
        noting
        """
        specfile = select_file(os.getcwd())
        if specfile is not None:
            self.spec_file_button.setStyleSheet("Text-align:left")
            self.spec_file_button.setText(specfile)
            if self.add_config:
                self.extended.parse_spec()
        else:
            self.spec_file_button.setText('')

        if self.main_win.is_exp_exists():
            self.save_conf()


    def set_dark_file(self):
        """
        It display a select dialog for user to select a darkfield file.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        darkfield_filename = select_file(os.getcwd())
        if darkfield_filename is not None:
            self.dark_file_button.setStyleSheet("Text-align:left")
            self.dark_file_button.setText(darkfield_filename)
        else:
            self.dark_file_button.setText('')


    def set_white_file(self):
        """
        It display a select dialog for user to select a whitefield file.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        whitefield_filename = select_file(os.getcwd())
        if whitefield_filename is not None:
            self.white_file_button.setStyleSheet("Text-align:left")
            self.white_file_button.setText(whitefield_filename)
        else:
            self.white_file_button.setText('')


    def set_data_dir(self):
        """
        It display a select dialog for user to select a directory with raw data file.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        data_dir = select_dir(os.getcwd())
        if data_dir is not None:
            self.data_dir_button.setStyleSheet("Text-align:left")
            self.data_dir_button.setText(data_dir)
        else:
            self.data_dir_button.setText('')


    def clear_conf(self):
        self.spec_file_button.setText('')
        self.data_dir_button.setText('')
        self.dark_file_button.setText('')
        self.white_file_button.setText('')
        self.det_roi.setText('')
        self.beam_zero.setText('')
        self.Imult.setText('')
        if self.add_config:
            self.extended.clear_conf()


    def load_instr_conf(self):
        """
        It display a select dialog for user to select a configuration file. When selected, the parameters
        from that file will be loaded to the window.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        instr_file = select_file(os.getcwd())
        if instr_file is not None:
            conf_map = ut.read_config(instr_file)
            self.load_tab(conf_map)
        else:
            msg_window('please select valid instrument config file')


    def get_instr_config(self):
        """
        It reads parameters related to instrument from the window into a dictionary.
        Parameters
        ----------
        none
        Returns
        -------
        conf_map : dict
            contains parameters read from window
        """
        conf_map = {}
        if len(self.spec_file_button.text()) > 0:
            conf_map['specfile'] = str(self.spec_file_button.text())
        if len(self.data_dir_button.text().strip()) > 0:
            conf_map['data_dir'] = str(self.data_dir_button.text()).strip()
        if len(self.dark_file_button.text().strip()) > 0:
            conf_map['darkfield_filename'] = str(self.dark_file_button.text().strip())
        if len(self.white_file_button.text().strip()) > 0:
            conf_map['whitefield_filename'] = str(self.white_file_button.text().strip())
        if len(self.Imult.text()) > 0:
            conf_map['Imult'] = ast.literal_eval(str(self.Imult.text()).replace(os.linesep,''))
        if len(self.det_roi.text()) > 0:
            conf_map['det_roi'] = ast.literal_eval(str(self.det_roi.text()).replace(os.linesep,''))
        if len(self.beam_zero.text()) > 0:
            conf_map['beam_zero'] = ast.literal_eval(str(self.beam_zero.text()).replace(os.linesep,''))

        if self.add_config:
            conf_map.update(self.extended.get_instr_config())

        return conf_map


    def save_conf(self):
        """
        Reads the parameters needed by format display script. Saves the config_instr configuration file with parameters from the window and runs the display script.
        Parameters
        ----------
        none
        Returns
        -------
        nothing
        """
        if not self.main_win.is_exp_exists():
            msg_window('the experiment does not exist, cannot save the config_instr file')
            return

        conf_map = self.get_instr_config()
        if len(conf_map) == 0:
            return

        er_msg = ver.verify('config_instr', conf_map)
        if len(er_msg) > 0:
            msg_window(er_msg)
            if not self.main_win.no_verify:
                return

        ut.write_config(conf_map, ut.join(self.main_win.experiment_dir, 'conf', 'config_instr'))

