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
import cohere_beamlines.Petra3_P10.beam_verifier as ver
import cohere_beamlines.Petra3_P10.diffractometers as diff
import cohere_beamlines.Petra3_P10.instrument as instr


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

        self.fio_widget = QWidget()
        fio_layout = QFormLayout()
        self.fio_widget.setLayout(fio_layout)
        self.energy = QLineEdit()
        self.energy.setModified(False)
        fio_layout.addRow("energy", self.energy)
        self.delta = QLineEdit()
        self.delta.setModified(False)
        fio_layout.addRow("delta (deg)", self.delta)
        self.gamma = QLineEdit()
        self.gamma.setModified(False)
        fio_layout.addRow("gamma (deg)", self.gamma)
        self.detdist = QLineEdit()
        self.detdist.setModified(False)
        fio_layout.addRow("detdist (mm)", self.detdist)
        self.mu = QLineEdit()
        self.mu.setModified(False)
        fio_layout.addRow("mu ", self.mu)
        self.om = QLineEdit()
        self.om.setModified(False)
        fio_layout.addRow("om ", self.om)
        self.chi = QLineEdit()
        self.chi.setModified(False)
        fio_layout.addRow("chi (deg)", self.chi)
        self.phi = QLineEdit()
        self.phi.setModified(False)
        fio_layout.addRow("phi (deg)", self.phi)
        self.scanmot = QLineEdit()
        self.scanmot.setModified(False)
        fio_layout.addRow("scan motor", self.scanmot)
        self.scan_step = QLineEdit()
        self.scan_step.setModified(False)
        fio_layout.addRow("scan step size", self.scan_step)
        self.detector = QLineEdit()
        self.detector.setModified(False)
        fio_layout.addRow("detector", self.detector)

        self.energy.textChanged.connect(lambda: set_overriden(self.energy))
        self.delta.textChanged.connect(lambda: set_overriden(self.delta))
        self.gamma.textChanged.connect(lambda: set_overriden(self.gamma))
        self.detdist.textChanged.connect(lambda: set_overriden(self.detdist))
        self.mu.textChanged.connect(lambda: set_overriden(self.mu))
        self.om.textChanged.connect(lambda: set_overriden(self.om))
        self.chi.textChanged.connect(lambda: set_overriden(self.chi))
        self.phi.textChanged.connect(lambda: set_overriden(self.phi))
        self.scanmot.textChanged.connect(lambda: set_overriden(self.scanmot))
        self.scan_step.textChanged.connect(lambda: set_overriden(self.scan_step))
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
        def override_item(item, value):
            item.setText(value)
            item.setStyleSheet('color: black')
            item.setModified(True)

        self.parse_foi()

        # if parameters are configured, override the readings from fio file
        if 'energy' in conf_map:
            override_item(self.energy, str(conf_map['energy']).replace(" ", ""))
        if 'del' in conf_map:
            override_item(self.delta, str(conf_map['del']).replace(" ", ""))
        if 'gam' in conf_map:
            override_item(self.gamma, str(conf_map['gam']).replace(" ", ""))
        if 'detdist' in conf_map:
            override_item(self.detdist, str(conf_map['detdist']).replace(" ", ""))
        if 'om' in conf_map:
            override_item(self.om, str(conf_map['om']).replace(" ", ""))
        if 'mu' in conf_map:
            override_item(self.mu, str(conf_map['mu']).replace(" ", ""))
        if 'chi' in conf_map:
            override_item(self.chi, str(conf_map['chi']).replace(" ", ""))
        if 'phi' in conf_map:
            override_item(self.phi, str(conf_map['phi']).replace(" ", ""))
        if 'scanmot' in conf_map:
            override_item(self.scanmot, str(conf_map['scanmot']).replace(" ", ""))
        if 'scan_step' in conf_map:
            override_item(self.scan_step, str(conf_map['scan_step']).replace(" ", ""))
        if 'detector' in conf_map:
            override_item(self.detector, str(conf_map['detector']).replace(" ", ""))


    def clear_conf(self):
        self.energy.setText('')
        self.delta.setText('')
        self.gamma.setText('')
        self.detdist.setText('')
        self.mu.setText('')
        self.om.setText('')
        self.chi.setText('')
        self.phi.setText('')
        self.scanmot.setText('')
        self.scan_step.setText('')
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
        if self.energy.isModified() and len(self.energy.text()) > 0:
            conf_map['energy'] = ast.literal_eval(str(self.energy.text()))
        if self.delta.isModified() and len(self.delta.text()) > 0:
            conf_map['del'] = ast.literal_eval(str(self.delta.text()))
        if self.gamma.isModified() and len(self.gamma.text()) > 0:
            conf_map['gam'] = ast.literal_eval(str(self.gamma.text()))
        if self.detdist.isModified() and len(self.detdist.text()) > 0:
            conf_map['detdist'] = ast.literal_eval(str(self.detdist.text()))
        if self.mu.isModified() and len(self.mu.text()) > 0:
            conf_map['mu'] = ast.literal_eval(str(self.mu.text()))
        if self.om.isModified() and len(self.om.text()) > 0:
            conf_map['om'] = ast.literal_eval(str(self.om.text()))
        if self.chi.isModified() and len(self.chi.text()) > 0:
            conf_map['chi'] = ast.literal_eval(str(self.chi.text()))
        if self.phi.isModified() and len(self.phi.text()) > 0:
            conf_map['phi'] = ast.literal_eval(str(self.phi.text()))
        if self.scanmot.isModified() and len(self.scanmot.text()) > 0:
            conf_map['scanmot'] = str(self.scanmot.text())
        if self.scan_step.isModified() and len(self.scan_step.text()) > 0:
            conf_map['scan_step'] = ast.literal_eval(str(self.scan_step.text()))
        if self.detector.isModified() and len(self.detector.text()) > 0:
            conf_map['detector'] = str(self.detector.text())

        return conf_map


    def parse_foi(self):
        """
        Calls utility function to parse fio file. Displas the parsed parameters in the window with blue text.
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
            msg_window ('cannot parse fio, scan not defined')
            return

        try:
            diff_obj = diff.Diffractometer()
        except Exception as e:
            msg_window (str(e))
            return

        data_dir = self.instr_tab.data_dir_button.text()
        if len(data_dir) == 0:
            msg_window ('data_dir not defined')
            return

        sample = self.instr_tab.sample.text()
        if len(sample) == 0:
            msg_window ('sample not defined')
            return

        instrument = instr.Instrument_Petra3_P10(None, diff_obj, None)

        first_scan = int(scan.split('-')[0].split(',')[0])
        fio_dict = instrument.parse_metadata(first_scan, data_dir=data_dir, sample=sample)
        if fio_dict is None:
            return
        if 'energy' in fio_dict:
            set_item_parsed(self.energy, str(fio_dict['energy']))
        if 'del' in fio_dict:
            set_item_parsed(self.delta, str(fio_dict['del']))
        if 'gam' in fio_dict:
            set_item_parsed(self.gamma, str(fio_dict['gam']))
        if 'om' in fio_dict:
            set_item_parsed(self.om, str(fio_dict['om']))
        if 'mu' in fio_dict:
            set_item_parsed(self.mu, str(fio_dict['mu']))
        if 'chi' in fio_dict:
            set_item_parsed(self.chi, str(fio_dict['chi']))
        if 'phi' in fio_dict:
            set_item_parsed(self.phi, str(fio_dict['phi']))
        if 'detdist' in fio_dict:
            set_item_parsed(self.detdist, str(fio_dict['detdist']))
        if 'scanmot' in fio_dict:
            set_item_parsed(self.scanmot, str(fio_dict['scanmot']))
        if 'scan_step' in fio_dict:
            set_item_parsed(self.scan_step, str(fio_dict['scan_step']))
        if 'detector' in fio_dict:
            set_item_parsed(self.detector, str(fio_dict['detector']))


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
            self.extended.fio_widget.hide()
        else:
            self.add_config = True
            self.extended.fio_widget.show()
            self.extended.parse_foi()
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
        self.data_dir_button = QPushButton()
        gen_layout.addRow("data dir", self.data_dir_button)
        self.sample = QLineEdit()
        gen_layout.addRow("sample", self.sample)
        tab_layout.addLayout(gen_layout)
        self.dark_file_button = QPushButton()
        gen_layout.addRow("darkfield file", self.dark_file_button)
        self.detector_module = QLineEdit()
        gen_layout.addRow("detector module", self.detector_module)
        self.beam_zero = QLineEdit()
        gen_layout.addRow("beam zero position [x, y]", self.beam_zero)
        tab_layout.addWidget(self.extended.fio_widget)
        if not self.add_config:
            self.extended.fio_widget.hide()
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

        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.dark_file_button.clicked.connect(self.set_dark_file)
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
        if 'data_dir' in conf_map:
            if os.path.isdir(conf_map['data_dir']):
                self.data_dir_button.setStyleSheet("Text-align:left")
                self.data_dir_button.setText(conf_map['data_dir'])
            else:
                msg_window(f'The data_dir directory in config_prep file {conf_map["data_dir"]} does not exist')
        else:
            self.data_dir_button.setText('')
        if 'sample' in conf_map:
            diff = str(conf_map['sample']).replace(" ", "")
            self.sample.setText(diff)
        if 'darkfield_filename' in conf_map:
            if os.path.isfile(conf_map['darkfield_filename']):
                self.dark_file_button.setStyleSheet("Text-align:left")
                self.dark_file_button.setText(conf_map['darkfield_filename'])
            else:
                msg_window(f'The darkfield file {conf_map["darkfield_filename"]} in config_prep file does not exist')
                self.dark_file_button.setText('')
        else:
            self.dark_file_button.setText('')
        if 'detector_module' in conf_map:
            self.detector_module.setText(str(conf_map['detector_module']).replace(" ", ""))
        if 'beam_zero' in conf_map:
            self.beam_zero.setText(str(conf_map['beam_zero']).replace(" ", ""))
            self.beam_zero.setStyleSheet('color: black')
        if self.add_config:
            self.extended.load_tab(conf_map)


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


    def clear_conf(self):
        self.data_dir_button.setText('')
        self.sample.setText('')
        if self.add_config:
            self.extended.clear_conf()
        self.dark_file_button.setText('')
        self.detector_module.setText('')
        self.beam_zero.setText('')


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
        if len(self.data_dir_button.text()) > 0:
            conf_map['data_dir'] = str(self.data_dir_button.text())
        if len(self.sample.text()) > 0:
            conf_map['sample'] = str(self.sample.text())
        if len(self.dark_file_button.text().strip()) > 0:
            conf_map['darkfield_filename'] = str(self.dark_file_button.text().strip())
        if len(self.detector_module.text()) > 0:
            conf_map['detector_module'] = ast.literal_eval(str(self.detector_module.text()))
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
        er_msg = ver.verify('config_instr', conf_map)
        if len(er_msg) > 0:
            msg_window(er_msg)
            if not self.main_win.no_verify:
                return

        if len(conf_map) == 0:
            return
        ut.write_config(conf_map, ut.join(self.main_win.experiment_dir, 'conf', 'config_instr'))


