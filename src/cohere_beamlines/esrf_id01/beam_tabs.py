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
import cohere_beamlines.esrf_id01.beam_verifier as ver


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


class InstrTab(QWidget):
    def __init__(self, parent=None):
        """
        Constructor, initializes the tabs.
        """
        super(InstrTab, self).__init__(parent)
        self.name = 'Instrument'
        self.conf_name = 'config_instr'


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

        tab_layout = QVBoxLayout()
        gen_layout = QFormLayout()
        self.detector_button = QLineEdit()
        gen_layout.addRow("detector name", self.detector_button)
        self.beam_zero = QLineEdit()
        gen_layout.addRow("beam zero position [x, y]", self.beam_zero)
        self.h5file_button = QPushButton()
        gen_layout.addRow("h5file file", self.h5file_button)
        tab_layout.addLayout(gen_layout)
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

        self.h5file_button.clicked.connect(self.set_h5file)
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
        if 'detector' in conf_map:
            self.detector_button.setStyleSheet("Text-align:left")
            self.detector_button.setText(conf_map['detector'])
        else:
            self.detector_button.setText('')
        if 'beam_zero' in conf_map:
            self.beam_zero.setText(str(conf_map['beam_zero']).replace(" ", ""))
            self.beam_zero.setStyleSheet('color: black')
        if 'h5file' in conf_map:
            h5file = conf_map['h5file']
            if os.path.isfile(h5file):
                self.h5file_button.setStyleSheet("Text-align:left")
                self.h5file_button.setText(h5file)
            else:
                msg_window(f'The h5file file {h5file} in config file does not exist')


    def set_h5file(self):
        """
        Calls selection dialog. The selected h5 file is parsed.
        The h5file is saved in config.
        Parameters
        ----------
        none
        Returns
        -------
        noting
        """
        h5file = select_file(os.getcwd())
        if h5file is not None:
            self.h5file_button.setStyleSheet("Text-align:left")
            self.h5file_button.setText(h5file)
        else:
            self.h5file_button.setText('')

        self.save_conf()


    def clear_conf(self):
        self.detector_button.setText('')
        self.beam_zero.setText('')
        self.h5file_button.setText('')


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
        if len(self.detector_button.text()) > 0:
            conf_map['detector'] = str(self.detector_button.text()).strip()
        if len(self.beam_zero.text()) > 0:
            conf_map['beam_zero'] = ast.literal_eval(str(self.beam_zero.text()).replace(os.linesep,''))
        if len(self.h5file_button.text()) > 0:
            conf_map['h5file'] = str(self.h5file_button.text())

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

        # verify here
        er_msg = ver.verify('config_instr', conf_map)
        if len(er_msg) > 0:
            msg_window(er_msg)
            if not self.main_win.no_verify:
                return

        ut.write_config(conf_map, ut.join(self.main_win.experiment_dir, 'conf', 'config_instr'))

