# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import ast
from pathlib import Path
import cohere_core.utilities as ut
import cohere_core.utilities.config_verifier as ver
import cohere_beamlines.aps_28idb.instr_schema as instr_schema
import cohere_beamlines.aps_28idb.instrument as instr
import cohere_beamlines.aps_28idb.diffractometers as diff
import cohere_beamlines.aps_28idb as bl
import cohere_beamlines.common.instr_tab as common


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
    item.setModified(True)
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
        self.energy.setModified(False)
        spec_layout.addRow("energy", self.energy)
        self.nu = QLineEdit()
        self.nu.setModified(False)
        spec_layout.addRow("nu (deg)", self.nu)
        self.delta = QLineEdit()
        self.delta.setModified(False)
        spec_layout.addRow("del (deg)", self.delta)
        self.mu = QLineEdit()
        self.mu.setModified(False)
        spec_layout.addRow("mu (deg)", self.mu)
        self.eta = QLineEdit()
        self.eta.setModified(False)
        spec_layout.addRow("eta (deg)", self.eta)
        self.chi = QLineEdit()
        self.chi.setModified(False)
        spec_layout.addRow("chi (deg)", self.chi)
        self.phi = QLineEdit()
        self.phi.setModified(False)
        spec_layout.addRow("phi (deg)", self.phi)
        self.scanmot = QLineEdit()
        self.scanmot.setModified(False)
        spec_layout.addRow("scan motor", self.scanmot)
        self.scan_step = QLineEdit()
        self.scan_step.setModified(False)
        spec_layout.addRow("scan step size", self.scan_step)

        self.energy.textChanged.connect(lambda: set_overriden(self.energy))
        self.delta.textChanged.connect(lambda: set_overriden(self.delta))
        self.nu.textChanged.connect(lambda: set_overriden(self.nu))
        self.mu.textChanged.connect(lambda: set_overriden(self.mu))
        self.eta.textChanged.connect(lambda: set_overriden(self.eta))
        self.chi.textChanged.connect(lambda: set_overriden(self.chi))
        self.phi.textChanged.connect(lambda: set_overriden(self.phi))
        self.scanmot.textChanged.connect(lambda: set_overriden(self.scanmot))
        self.scan_step.textChanged.connect(lambda: set_overriden(self.scan_step))


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
        def override_item(item, value):
            item.setText(value)
            item.setStyleSheet('color: black')
            item.setModified(True)

        self.parse_spec()

        # if parameters are configured, override the readings from spec file
        if 'energy' in conf_map:
            override_item(self.energy, str(conf_map['energy']).replace(" ", ""))
        if 'del' in conf_map:
            override_item(self.delta, str(conf_map['del']).replace(" ", ""))
        if 'nu' in conf_map:
            override_item(self.nu, str(conf_map['nu']).replace(" ", ""))
        if 'mu' in conf_map:
            override_item(self.mu, str(conf_map['mu']).replace(" ", ""))
        if 'eta' in conf_map:
            override_item(self.eta, str(conf_map['eta']).replace(" ", ""))
        if 'chi' in conf_map:
            override_item(self.chi, str(conf_map['chi']).replace(" ", ""))
        if 'phi' in conf_map:
            override_item(self.phi, str(conf_map['phi']).replace(" ", ""))
        if 'scanmot' in conf_map:
            override_item(self.scanmot, str(conf_map['scanmot']).replace(" ", ""))
        if 'scan_step' in conf_map:
            override_item(self.scan_step, str(conf_map['scan_step']).replace(" ", ""))


    def clear_conf(self):
        self.energy.setText('')
        self.delta.setText('')
        self.nu.setText('')
        self.mu.setText('')
        self.eta.setText('')
        self.chi.setText('')
        self.phi.setText('')
        self.scanmot.setText('')
        self.scan_step.setText('')


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
        if self.energy.isModified() and len(self.energy.text()) > 0:
            conf_map['energy'] = ast.literal_eval(str(self.energy.text()))
        if self.delta.isModified() and len(self.delta.text()) > 0:
            conf_map['del'] = ast.literal_eval(str(self.delta.text()))
        if self.nu.isModified() and len(self.nu.text()) > 0:
            conf_map['nu'] = ast.literal_eval(str(self.nu.text()))
        if self.mu.isModified() and len(self.mu.text()) > 0:
            conf_map['mu'] = ast.literal_eval(str(self.mu.text()))
        if self.eta.isModified() and len(self.eta.text()) > 0:
            conf_map['eta'] = ast.literal_eval(str(self.eta.text()))
        if self.chi.isModified() and len(self.chi.text()) > 0:
            conf_map['chi'] = ast.literal_eval(str(self.chi.text()))
        if self.phi.isModified() and len(self.phi.text()) > 0:
            conf_map['phi'] = ast.literal_eval(str(self.phi.text()))
        if self.scanmot.isModified() and len(self.scanmot.text()) > 0:
            conf_map['scanmot'] = str(self.scanmot.text())
        if self.scan_step.isModified() and len(self.scan_step.text()) > 0:
            conf_map['scan_step'] = ast.literal_eval(str(self.scan_step.text()))

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
        def set_item_parsed(item, value):
            item.setText(value)
            item.setModified(False)
            item.setStyleSheet('color: blue')

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

        diff_name = self.instr_tab.diffractometer.currentText()
        if len(diff_name) == 0:
            msg_window ('cannot parse spec, diffractometer not defined')
            return
        try:
            diff_obj = diff.create_diffractometer(diff_name)
        except Exception as e:
            msg_window (str(e))
            return

        first_scan = int(scan.split('-')[0].split(',')[0])
        instrument = instr.Instrument_aps_28idb(None, diff_obj, None)
        spec_dict = instrument.parse_metadata(first_scan, specfile=specfile)
        if spec_dict is None:
            return
        if 'energy' in spec_dict:
            set_item_parsed(self.energy, str(spec_dict['energy']))
        if 'del' in spec_dict:
            set_item_parsed(self.delta, str(spec_dict['del']))
        if 'nu' in spec_dict:
            set_item_parsed(self.nu, str(spec_dict['nu']))
        if 'eta' in spec_dict:
            set_item_parsed(self.eta, str(spec_dict['eta']))
        if 'chi' in spec_dict:
            set_item_parsed(self.chi, str(spec_dict['chi']))
        if 'phi' in spec_dict:
            set_item_parsed(self.phi, str(spec_dict['phi']))
        if 'mu' in spec_dict:
            set_item_parsed(self.mu, str(spec_dict['mu']))
        if 'scanmot' in spec_dict:
            set_item_parsed(self.scanmot, str(spec_dict['scanmot']))
        if 'scan_step' in spec_dict:
            set_item_parsed(self.scan_step, str(spec_dict['scan_step']))


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
        self.detector = QLineEdit()
        gen_layout.addRow("detector", self.detector)
        self.detdist = QLineEdit()
        gen_layout.addRow("detdist (mm)", self.detdist)
        self.det_roi = QLineEdit()
#        gen_layout.addRow("detector area (det_roi)", self.det_roi)
        self.beam_zero = QLineEdit()
        gen_layout.addRow("beam zero position [x, y]", self.beam_zero)
        self.diffractometer = QComboBox()
        self.diffractometer.addItem("")
        self.diffractometer.addItem("tower")
        self.diffractometer.addItem("huber")
        gen_layout.addRow("diffractometer", self.diffractometer)
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
        self.detector.textChanged.connect(lambda: set_overriden(self.detector))
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
                msg_window(f'The data_dir directory in config_instr file {conf_map["data_dir"]} does not exist')
        else:
            self.data_dir_button.setText('')
        if 'darkfield_filename' in conf_map:
            if os.path.isfile(conf_map['darkfield_filename']):
                self.dark_file_button.setStyleSheet("Text-align:left")
                self.dark_file_button.setText(conf_map['darkfield_filename'])
            else:
                msg_window(f'The darkfield file {conf_map["darkfield_filename"]} in config_instr file does not exist, getting from git repository')
                self.dark_file_button.setText('')
        else:
            self.dark_file_button.setText('')
        if 'whitefield_filename' in conf_map:
            if os.path.isfile(conf_map['whitefield_filename']):
                self.white_file_button.setStyleSheet("Text-align:left")
                self.white_file_button.setText(conf_map['whitefield_filename'])
            else:
                self.white_file_button.setText('')
                msg_window(f'The whitefield file {conf_map["whitefield_filename"]} in config_instr file does not exist, getting from git repository')
        else:
            self.white_file_button.setText('')
        if 'Imult' in conf_map:
            self.Imult.setText(str(conf_map['Imult']).replace(" ", ""))
        if 'detector' in conf_map:
            self.detector.setText(str(conf_map['detector']).replace(" ", ""))
            self.detector.setStyleSheet('color: black')
            self.detector.setModified(True)
        if 'detdist' in conf_map:
            self.detdist.setText(str(conf_map['detdist']).replace(" ", ""))
            self.detdist.setStyleSheet('color: black')
            self.detdist.setModified(True)

        if 'det_roi' in conf_map:
            self.det_roi.setText(str(conf_map['det_roi']).replace(" ", ""))
            self.det_roi.setStyleSheet('color: black')
            self.det_roi.setModified(True)
        if 'beam_zero' in conf_map:
            self.beam_zero.setText(str(conf_map['beam_zero']).replace(" ", ""))
            self.beam_zero.setStyleSheet('color: black')
        if 'diffractometer' in conf_map:
            if conf_map['diffractometer'] == 'tower':
                self.diffractometer.setCurrentIndex(1)
            elif conf_map['diffractometer'] == 'huber':
                self.diffractometer.setCurrentIndex(2)
            else:
                self.diffractometer.setCurrentIndex(0)
        else:
            self.diffractometer.setCurrentIndex(0)

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
        start_dir = os.path.join(Path(bl.__file__).parents[0], 'detector_corrections')
        darkfield_filename = select_file(start_dir)
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
        start_dir = os.path.join(Path(bl.__file__).parents[0], 'detector_corrections')
        whitefield_filename = select_file(start_dir)
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
        self.diffractometer.setCurrentIndex(0)
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
        if self.detector.isModified() and len(self.detector.text()) > 0:
            conf_map['detector'] = str(self.detector.text())
        if len(self.detdist.text()) > 0:
            conf_map['detdist'] = ast.literal_eval(str(self.detdist.text()))
        if self.det_roi.isModified() and len(self.det_roi.text()) > 0:
            conf_map['det_roi'] = ast.literal_eval(str(self.det_roi.text()).replace(os.linesep,''))
        if len(self.beam_zero.text()) > 0:
            conf_map['beam_zero'] = ast.literal_eval(str(self.beam_zero.text()).replace(os.linesep,''))
        if self.diffractometer.currentIndex() == 1:
            conf_map['diffractometer'] = 'tower'
        if self.diffractometer.currentIndex() == 2:
            conf_map['diffractometer'] = 'huber'

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

        er_msg = ver.verify_types(instr_schema.get_config_schema(), conf_map)
        if len(er_msg) > 0:
            msg_window(er_msg)
            if not self.main_win.no_verify:
                return

        ut.write_config(conf_map, ut.join(self.main_win.experiment_dir, 'conf', 'config_instr'))

