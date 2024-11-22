import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QButtonGroup
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import QtWidgets, uic
import usb.backend
import usb.backend.libusb1
import json
from usb.core import find as find_usb
import usb
import os
import socket
import pyodbc

class DashboardWindow(QMainWindow):
    def __init__(self):
        super(DashboardWindow, self).__init__()

        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.config_path = r'C:\barcode\barcode.json'
        # Load the UI file first
        uic.loadUi(self.resource_path("ui/dashboard.ui"), self)
        self.setWindowIcon(QIcon(self.resource_path("images/logo.ico")))
        self.setWindowTitle("Dashboard")
        self.setFixedSize(1212, 760)

        # Alternatively, set the maximum size equal to the minimum size to prevent maximizing
        self.setMaximumSize(1212, 760)
        self.setMinimumSize(1212, 760)

        background = QPixmap(self.resource_path("images/background.jpg"))

        #Initialize widgets
        self.lbl_bg = self.findChild(QtWidgets.QLabel, "lbl_background")
        self.lbl_bg.setPixmap(background)
        self.lbl_dashboardIcon = self.findChild(QtWidgets.QLabel, "dashboard_icon")
        self.lbl_dashboardIcon.setPixmap(QPixmap(self.resource_path("images/dashboard.png")))
        self.lbl_resultConnectedDevice = self.findChild(QtWidgets.QLabel, "lbl_connectedDevicesResult")
        self.lbl_resultConnectivity = self.findChild(QtWidgets.QLabel, "lbl_connectivityResult")
        self.lbl_resultDatabase = self.findChild(QtWidgets.QLabel, "lbl_databaseResult")
        self.lbl_resultConfiguration = self.findChild(QtWidgets.QLabel, "lbl_configurationFileResult")
        self.lbl_loggingResult = self.findChild(QtWidgets.QLabel, "lbl_loggingResult")
        self.btn_checkConnectedDevices = self.findChild(QtWidgets.QPushButton, "btn_checkConnectedDevices")
        self.btn_checkConnectedDevices.clicked.connect(self.count_connected_printers)
        self.btn_ping = self.findChild(QtWidgets.QPushButton, "btn_ping")
        self.btn_ping.clicked.connect(self.is_connected)
        self.btn_reloadDatabase = self.findChild(QtWidgets.QPushButton, "btn_reloadDatabase")
        self.btn_reloadDatabase.clicked.connect(self.can_connect_to_database)
        self.btn_checkConfiguration = self.findChild(QtWidgets.QPushButton, "btn_checkConfiguration")
        self.btn_checkConfiguration.clicked.connect(self.check_config_file)
        self.btn_checkLogging = self.findChild(QtWidgets.QPushButton, "btn_checkLogging")
        self.btn_checkLogging.clicked.connect(self.check_logging_enabled)
        self.btn_reloadTableView = self.findChild(QtWidgets.QPushButton, "btn_reloadTableView")
        self.btn_reloadTableView.clicked.connect(self.reload_tableview)
        self.btn_reloadPrinterInformation = self.findChild(QtWidgets.QPushButton, "btn_reloadPrinterInformation")
        self.btn_reloadPrinterInformation.clicked.connect(self.reload_current_printer_info)
        self.et_enterToSearch = self.findChild(QtWidgets.QLineEdit, "et_enterToSearch")
        self.et_itemCount = self.findChild(QtWidgets.QLineEdit, "et_itemCount")
        self.et_printerVid = self.findChild(QtWidgets.QLineEdit, "et_printerVid")
        self.et_printerPid = self.findChild(QtWidgets.QLineEdit, "et_printerPid")
        self.btn_close = self.findChild(QtWidgets.QPushButton, "btn_close")
        self.btn_close.clicked.connect(self.close)
        self.btn_reload = self.findChild(QtWidgets.QPushButton, "btn_reload")
        self.btn_reload.clicked.connect(self.load_data)
        self.btn_about = self.findChild(QtWidgets.QPushButton, "btn_about")

        #Icon section
        self.logo_icon = self.findChild(QtWidgets.QLabel, "lbl_iconLogo")
        logoIcon = QPixmap(self.resource_path("images/logo.jpeg"))
        databaseIcon = QPixmap(self.resource_path("images/database.png"))
        printerIcon = QPixmap(self.resource_path("images/printer.png"))
        otherSettingsIcon = QPixmap(self.resource_path("images/settings.png"))
        loggingIcon = QPixmap(self.resource_path("images/log.png"))
        connectivityIcon = QPixmap(self.resource_path("images/connect.png"))
        tableIcon  = QPixmap(self.resource_path("images/table.png"))
        self.logo_icon.setPixmap(logoIcon)

        self.icon_database = self.findChild(QtWidgets.QLabel, "lbl_iconDatabase")
        self.icon_printer = self.findChild(QtWidgets.QLabel, "lbl_iconPrinter")
        self.icon_other_settings = self.findChild(QtWidgets.QLabel, "lbl_iconOtherSettings")
        self.icon_logging = self.findChild(QtWidgets.QLabel, "lbl_iconLogging")
        self.icon_connectivity = self.findChild(QtWidgets.QLabel, "lbl_iconConnectivity")
        self.icon_table = self.findChild(QtWidgets.QLabel, "lbl_iconTable")
        self.icon_printer2 = self.findChild(QtWidgets.QLabel, "lbl_iconPrinter_2")
        
        self.icon_database.setPixmap(databaseIcon)
        self.icon_printer.setPixmap(printerIcon)
        self.icon_other_settings.setPixmap(otherSettingsIcon)
        self.icon_logging.setPixmap(loggingIcon)
        self.icon_connectivity.setPixmap(connectivityIcon)
        self.icon_table.setPixmap(tableIcon)
        self.icon_printer2.setPixmap(printerIcon)

        self.load_data()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def is_connected(self):
        try:
            # Try to connect to a public DNS server (Google's DNS: 8.8.8.8) over port 53 (DNS port)
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            self.lbl_resultConnectivity.setText("✅️")
        except (socket.timeout, OSError):
            self.lbl_resultConnectivity.setText("❌")
        
    def can_connect_to_database(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={config["server"]};"
                    f"DATABASE={config['database']};"
                    f"UID={config['username']};"
                    f"PWD={config['password']};"
                )
                with pyodbc.connect(connection_string, timeout=5) as connection:
                # Connection successful
                    self.lbl_resultDatabase.setText("✅️")
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)
        except pyodbc.Error as e:
            print(f"Connection failed: {e}")
            self.lbl_resultDatabase.setText("❌")
        
    def check_config_file(self):
        # Check if the file exists
        required_keys = [
            "server",
            "database",
            "username",
            "password",
            "vid",
            "pid",
            "endpoint",
            "companyName",
            "location",
            "useZPL",
            "ip_address",
            "wireless_mode",
            "zplTemplate",
            "tpslTemplate",
            "logging"
        ]
        if not os.path.isfile(self.config_path):
            print(f"Error: Configuration file not found at {self.config_path}")
            self.lbl_resultConfiguration.setText("❌")

        try:
            # Load and parse the JSON file
            with open(self.config_path, "r") as file:
                config = json.load(file)
        except json.JSONDecodeError:
            print("Error: Configuration file is not a valid JSON.")
            self.lbl_resultConfiguration.setText("❌")

        # Check for all required keys
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"Error: Missing required keys: {', '.join(missing_keys)}")
            self.lbl_resultConfiguration.setText("❌")
        self.lbl_resultConfiguration.setText("✅️")
    
    def count_connected_printers(self):
        try:
            # Find all USB devices
            devices = usb.core.find(find_all=True)
            printer_count = 0

            # Iterate over devices and check if any have the printer class (0x07)
            for device in devices:
                # The bDeviceClass is 7 for printers or can be 0 if the interface specifies it
                if device.bDeviceClass == 7:
                    printer_count += 1
                else:
                    # Check each configuration for interfaces specifying the printer class
                    for config in device:
                        for interface in config:
                            if interface.bInterfaceClass == 7:
                                printer_count += 1
                                break

            self.lbl_resultConnectedDevice.setText(str(printer_count))
        except usb.core.USBError as e:
            print(f"USB Error: {e}")
            self.lbl_resultConnectedDevice.setText(str("-1")) 
        except Exception as e:
            print(f"Error: {e}")
            self.lbl_resultConnectedDevice.setText(str("-1"))  
    
    def check_logging_enabled(self):
        try:
            # Load the JSON file
            with open(self.config_path, 'r') as file:
                config = json.load(file)
            
            # Check if 'logging' key exists
            if 'logging' not in config:
                return "Error: 'logging' key is missing in the configuration file."
            
            # Check if 'logging' value is a boolean
            if isinstance(config['logging'], bool):
                if config['logging']:
                    self.lbl_loggingResult.setText("✅️")
                    self.btn_checkLogging.setText("Enabled")
                else:
                    self.lbl_loggingResult.setText("❌")
                    self.btn_checkLogging.setText("Disabled")
            else:
                return "Error: 'logging' key must be a boolean (true or false)."
        except FileNotFoundError:
            return f"Error: Configuration file not found at {self.config_path}."
        except json.JSONDecodeError:
            return "Error: Configuration file is not a valid JSON."
        
    def reload_tableview(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.et_enterToSearch.setText(str(config["enterToSearch"]))
                self.et_itemCount.setText(config['itemCount'])
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def reload_current_printer_info(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.et_printerVid.setText(config["vid"])
                self.et_printerPid.setText(config['pid'])
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    
    def load_data(self):
        self.count_connected_printers()
        self.is_connected()
        self.can_connect_to_database()
        self.check_config_file()
        self.check_logging_enabled()
        self.reload_tableview()
        self.reload_current_printer_info()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec_())