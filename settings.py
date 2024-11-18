import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5 import QtWidgets, uic
from ui_mainwindow2 import Ui_MainWindow
import json
import os


class SettingsWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(SettingsWindow, self).__init__()

        # Load the UI file first
        self.setupUi(self)
        background = QPixmap(self.resource_path("background.jpg"))
        self.background = self.findChild(QtWidgets.QLabel, "img_label")
        self.background.setPixmap(background)

        self.settings_icon = self.findChild(QtWidgets.QLabel, "settings_icon")
        settingsIcon = QPixmap(self.resource_path("settingsicon.png"))
        self.settings_icon.setPixmap(settingsIcon)

        # Access UI elements after loading the UI file
        self.serverName = self.findChild(QtWidgets.QLineEdit, "et_serverName")
        self.databaseName = self.findChild(QtWidgets.QLineEdit, "et_databaseName")
        self.userName = self.findChild(QtWidgets.QLineEdit, "et_userName")
        self.password = self.findChild(QtWidgets.QLineEdit, "et_password")
        self.printerVid = self.findChild(QtWidgets.QLineEdit, "et_printerVid")
        self.printerPid = self.findChild(QtWidgets.QLineEdit, "et_printerPid")
        self.endpoint = self.findChild(QtWidgets.QLineEdit, "et_endPoint")
        self.command = self.findChild(QtWidgets.QLineEdit, "et_commandLanguage")
        self.companyName = self.findChild(QtWidgets.QLineEdit, "et_companyName")
        self.location = self.findChild(QtWidgets.QLineEdit, "et_location")
        self.tpslCommand = self.findChild(QtWidgets.QTextEdit, "et_tpslCommand")
        self.zplCommand = self.findChild(QtWidgets.QTextEdit, "et_zplCommand")

        self.cancelButton = self.findChild(QtWidgets.QPushButton, "btn_cancel")
        self.cancelButton.setCursor(Qt.PointingHandCursor)
        self.cancelButton.clicked.connect(self.close)
        self.saveButton = self.findChild(QtWidgets.QPushButton, "btn_save")
        self.saveButton.setCursor(Qt.PointingHandCursor)
        self.saveButton.clicked.connect(self.update_data)

        # Set the config path
        self.config_path = r'C:\barcode\barcode.json'

        # Load data from JSON file to UI elements
        self.load_data()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)


    def load_data(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.serverName.setText(config["server"])
                self.databaseName.setText(config['database'])
                self.userName.setText(config['username'])
                self.password.setText(config['password'])
                self.printerVid.setText(config['vid'])
                self.printerPid.setText(config['pid'])
                self.endpoint.setText(config['endpoint'])
                self.command.setText(config['commandLanguage'])
                self.companyName.setText(config['companyName'])
                self.location.setText(config['location'])
                self.tpslCommand.setText(config['tpslTemplate'])
                self.zplCommand.setText(config['zplTemplate'])
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def update_data(self):

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            config['server'] = self.serverName.text()
            config['database'] = self.databaseName.text()
            config['username'] = self.userName.text()
            config['password'] = self.password.text()
            config['vid'] = self.printerVid.text()
            config['pid'] = self.printerPid.text()
            config['endpoint'] = self.endpoint.text()
            config['companyName'] = self.companyName.text()
            config['location'] = self.location.text()
            config['commandLanguage'] = self.command.text()
            config['zplTemplate'] = self.zplCommand.toPlainText()
            config['tpslTemplate'] = self.tpslCommand.toPlainText()

            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)
                print("Succesfully updated!")
                self.close()
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

