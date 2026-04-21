# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
from PyQt6.QtCore import *
from PyQt56.QtWidgets import *
import ast
import cohere_core.utilities as ut
import cohere_beamlines.aps_20ide.diffractometers as diff
from cohere_beamlines.common.det import Detector as det


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
    dialog.setFileMode(QFileDialog.ExistingFile)
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

        self.meta_widget = QWidget()
        spec_layout = QFormLayout()
        self.meta_widget.setLayout(spec_layout)
        self.energy = QLineEdit()
        spec_layout.addRow("energy", self.energy)
        self.DetX = QLineEdit()
        spec_layout.addRow("DetX (mm)", self.DetX)
        self.DetY = QLineEdit()
        spec_layout.addRow("DetY (mm)", self.DetY)
        self.DetZ = QLineEdit()
        spec_layout.addRow("DetZ (mm)", self.DetZ)

        self.energy.textChanged.connect(lambda: set_overriden(self.energy))
        self.DetZ.textChanged.connect(lambda: set_overriden(self.DetZ))
        self.DetX.textChanged.connect(lambda: set_overriden(self.DetX))
        self.DetY.textChanged.connect(lambda: set_overriden(self.DetY))


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
        self.parse_metadata()

        # if parameters are configured, override the readings from spec file
        if 'energy' in conf_map:
            self.energy.setText(str(conf_map['energy']).replace(" ", ""))
            self.energy.setStyleSheet('color: black')
        if 'DetX' in conf_map:
            self.DetX.setText(str(conf_map['DetX']).replace(" ", ""))
            self.DetX.setStyleSheet('color: black')
        if 'DetY' in conf_map:
            self.DetY.setText(str(conf_map['DetY']).replace(" ", ""))
            self.DetY.setStyleSheet('color: black')
        if 'DetZ' in conf_map:
            self.DetZ.setText(str(conf_map['DetZ']).replace(" ", ""))
            self.DetZ.setStyleSheet('color: black')


    def clear_conf(self):
        self.energy.setText('')
        self.DetX.setText('')
        self.DetY.setText('')
        self.DetZ.setText('')


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
        if len(self.DetX.text()) > 0:
            conf_map['DetX'] = ast.literal_eval(str(self.DetX.text()))
        if len(self.DetY.text()) > 0:
            conf_map['DetY'] = ast.literal_eval(str(self.DetY.text()))
        if len(self.DetZ.text()) > 0:
            conf_map['DetZ'] = ast.literal_eval(str(self.DetZ.text()))

        return conf_map


    def parse_metadata(self):
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
            msg_window ('cannot parse metadata, scan not defined')
            return

        diffractometer = self.instr_tab.diffractometer.text()
        if len(diffractometer) == 0:
            msg_window ('cannot parse metadata, diffractometer not defined')
            return

        data_dir = self.instr_tab.data_dir_button.text()
        if len(data_dir) == 0:
            msg_window ('cannot parse metadata, data_dir not defined')
            return

        try:
            diff_obj = diff.create_diffractometer(diffractometer, {'data_dir' : data_dir})
        except Exception as e:
            msg_window (str(e))
            return

        last_scan = int(scan.split('-')[-1].split(',')[-1])
        meta_dict = diff_obj.parse_metadata(last_scan)
        if meta_dict is None:
            return
        if 'energy' in meta_dict:
            self.energy.setText(str(meta_dict['energy']))
            self.energy.setStyleSheet('color: blue')
        if 'DetX' in meta_dict:
            self.DetX.setText(str(meta_dict['DetX']))
            self.DetX.setStyleSheet('color: blue')
        if 'DetY' in meta_dict:
            self.DetY.setText(str(meta_dict['DetY']))
            self.DetY.setStyleSheet('color: blue')
        if 'DetZ' in meta_dict:
            self.DetZ.setText(str(meta_dict['DetZ']))
            self.DetZ.setStyleSheet('color: blue')


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
            self.extended.meta_widget.hide()
        else:
            self.add_config = True
            self.extended.meta_widget.show()
            self.extended.parse_metadata()
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
        self.diffractometer = QLineEdit()
        gen_layout.addRow("diffractometer", self.diffractometer)
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
        self.remove_band_background = None
        detector_layout = QFormLayout()
        self.set_detector_layout(detector_layout)
        gen_layout.addRow(detector_layout)
        tab_layout.addLayout(gen_layout)
        tab_layout.addWidget(self.extended.meta_widget)
        if not self.add_config:
            self.extended.meta_widget.hide()
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

        self.detector.textChanged.connect(lambda: self.set_detector_layout(detector_layout))
        self.data_dir_button.clicked.connect(self.set_data_dir)
        self.dark_file_button.clicked.connect(self.set_dark_file)
        self.white_file_button.clicked.connect(self.set_white_file)
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
        if 'diffractometer' in conf_map:
            diff = str(conf_map['diffractometer']).replace(" ", "")
            self.diffractometer.setText(diff)
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
                self.dark_file_button.setText('')
                msg_window(f'The darkfield file {conf_map["darkfield_filename"]} in config_prep file does not exist')
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
        if 'detector' in conf_map:
            self.detector.setText(str(conf_map['detector']).replace(" ", ""))
            self.detector.setStyleSheet('color: black')

        if self.remove_band_background is not None:
            self.remove_band_background.setChecked('remove_band_background' in conf_map and conf_map['remove_band_background'])
            if self.remove_band_background:
                if 'rbb_smooth_sigma' in conf_map:
                    self.rbb_smooth_sigma.setText(str(conf_map['rbb_smooth_sigma']))
                if 'rbb_robust' in conf_map and conf_map['rbb_robust']:
                    self.rbb_robust.setChecked(True)

        if self.add_config:
            self.extended.load_tab(conf_map)


    def toggle_rbb(self):
        if self.remove_band_background.isChecked():
            self.rbb_smooth_sigma = QLineEdit()
            self.rbb_smooth_sigma.setToolTip('if left blank, the sigma will default to detector optimal value')
            self.rbb_layout.addRow('rbb smooth sigma', self.rbb_smooth_sigma)
            self.rbb_robust = QCheckBox('rbb robust')
            self.rbb_robust.setToolTip('if robust, estimates are calculated by median, otherwise by mean')
            self.rbb_layout.addWidget(self.rbb_robust)
        else:
            for i in reversed(range(self.rbb_layout.count())):
                self.rbb_layout.itemAt(i).widget().setParent(None)

    def set_detector_layout(self, layout):
        if str(self.detector.text()) in det.det_bound_background:
            self.remove_band_background = QCheckBox('remove band bckground')
            layout.addWidget(self.remove_band_background)
            self.remove_band_background.setChecked(False)
            self.rbb_layout = QFormLayout()
            layout.addRow(self.rbb_layout)
        else:
            if self.remove_band_background is not None:
                self.remove_band_background.setChecked(False)
                self.remove_band_background.setParent(None)
            self.remove_band_background = None

        if self.remove_band_background is not None:
            self.remove_band_background.stateChanged.connect(self.toggle_rbb)


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
        if self.add_config:
            self.extended.parse_metadata()


    def clear_conf(self):
        self.diffractometer.setText('')
        self.data_dir_button.setText('')
        self.dark_file_button.setText('')
        self.white_file_button.setText('')
        self.Imult.setText('')
        self.detector.setText('')
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
        if len(self.diffractometer.text()) > 0:
            conf_map['diffractometer'] = str(self.diffractometer.text())
        if len(self.data_dir_button.text().strip()) > 0:
            conf_map['data_dir'] = str(self.data_dir_button.text()).strip()
        if len(self.dark_file_button.text().strip()) > 0:
            conf_map['darkfield_filename'] = str(self.dark_file_button.text().strip())
        if len(self.white_file_button.text().strip()) > 0:
            conf_map['whitefield_filename'] = str(self.white_file_button.text().strip())
        if len(self.Imult.text()) > 0:
            conf_map['Imult'] = ast.literal_eval(str(self.Imult.text()).replace(os.linesep,''))
        if len(self.detector.text()) > 0:
            conf_map['detector'] = str(self.detector.text())
        if self.remove_band_background is not None and self.remove_band_background.isChecked():
            conf_map['remove_band_background'] = ast.literal_eval(str(self.remove_band_background.isChecked()))
            if self.rbb_smooth_sigma.text().strip() != '':
                conf_map['rbb_smooth_sigma'] = ast.literal_eval(str(self.rbb_smooth_sigma.text()))
            if self.rbb_robust.isChecked():
                conf_map['rbb_robust'] = ast.literal_eval(str(self.rbb_robust.isChecked()))

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

        # # verify that disp configuration is ok
        # er_msg = ver.verify('config_instr', conf_map)

        ut.write_config(conf_map, ut.join(self.main_win.experiment_dir, 'conf', 'config_instr'))
