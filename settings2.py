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


class SettingsWindow(QMainWindow):
    def __init__(self):
        super(SettingsWindow, self).__init__()
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        # Load the UI file first
        uic.loadUi(self.resource_path("ui/settings2.ui"), self)
        self.setWindowIcon(QIcon(self.resource_path("images/logo.ico")))
        self.setWindowTitle("Settings")
        self.setFixedSize(1210, 696)

        # Alternatively, set the maximum size equal to the minimum size to prevent maximizing
        self.setMaximumSize(1210, 696)
        self.setMinimumSize(1210, 696)

        self.settings_icon = self.findChild(QtWidgets.QLabel, "settings_icon")
        settingsIcon = QPixmap(self.resource_path("images/setting.png"))
        databaseIcon = QPixmap(self.resource_path("images/database.png"))
        background = QPixmap(self.resource_path("images/background.jpg"))
        printerIcon = QPixmap(self.resource_path("images/printer.png"))
        logoIcon = QPixmap(self.resource_path("images/logo.jpeg"))
        otherSettingsIcon = QPixmap(self.resource_path("images/settings.png"))
        zplIcon = QPixmap(self.resource_path("images/zpl.png"))
        tpslIcon = QPixmap(self.resource_path("images/tpsl.png"))
        self.settings_icon.setPixmap(settingsIcon)
        self.cb_logging = self.findChild(QtWidgets.QCheckBox, 'cb_logging')


        # Icons Section
        self.lbl_bg = self.findChild(QtWidgets.QLabel, "lbl_background")
        self.lbl_bg.setPixmap(background)
        self.lbl_iconLogo = self.findChild(QtWidgets.QLabel, "lbl_iconLogo")
        self.lbl_iconLogo.setPixmap(logoIcon)
        self.icon_database = self.findChild(QtWidgets.QLabel, "lbl_iconDatabase")
        self.icon_printer = self.findChild(QtWidgets.QLabel, "lbl_iconPrinter")
        self.icon_other_settings = self.findChild(QtWidgets.QLabel, "lbl_iconOtherSettings")
        self.icon_zpl = self.findChild(QtWidgets.QLabel, "lbl_iconZpl")
        self.icon_tpsl = self.findChild(QtWidgets.QLabel, "lbl_iconTpsl")
        
        self.icon_database.setPixmap(databaseIcon)
        self.icon_printer.setPixmap(printerIcon)
        self.icon_other_settings.setPixmap(otherSettingsIcon)
        self.icon_zpl.setPixmap(zplIcon)
        self.icon_tpsl.setPixmap(tpslIcon)

        # Access UI elements after loading the UI file
        self.serverName = self.findChild(QtWidgets.QLineEdit, "et_serverName")
        self.databaseName = self.findChild(QtWidgets.QLineEdit, "et_databaseName")
        self.userName = self.findChild(QtWidgets.QLineEdit, "et_userName")
        self.password = self.findChild(QtWidgets.QLineEdit, "et_password")
        self.printer_list = self.findChild(QtWidgets.QComboBox, 'combo_printers')
        self.populate_printer_list()
        self.printer_list.currentIndexChanged.connect(self.update_printer_in_json)
        self.printerVid = self.findChild(QtWidgets.QLineEdit, "et_printerVid")
        self.printerPid = self.findChild(QtWidgets.QLineEdit, "et_printerPid")
        self.endpoint = self.findChild(QtWidgets.QLineEdit, "et_endPoint")
        self.ip_address = self.findChild(QtWidgets.QLineEdit, "et_ipAddress")
        self.wireless_mode = self.findChild(QtWidgets.QCheckBox, "cb_useIP")
        self.wireless_mode.stateChanged.connect(self.onWirelessModeStateChanged)
        self.onWirelessModeStateChanged()
        self.companyName = self.findChild(QtWidgets.QLineEdit, "et_companyName")
        self.location = self.findChild(QtWidgets.QLineEdit, "et_location")
        self.tpslCommand = self.findChild(QtWidgets.QTextEdit, "et_tpslCommand")
        self.use_tpsl = self.findChild(QtWidgets.QRadioButton, "rb_tpsl")
        self.zplCommand = self.findChild(QtWidgets.QTextEdit, "et_zplCommand")
        self.use_zpl = self.findChild(QtWidgets.QRadioButton, "rb_zpl")
        self.use_zpl.toggled.connect(self.onUseZPLStateChanged)
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.use_tpsl)
        self.button_group.addButton(self.use_zpl)
        self.onUseZPLStateChanged()

        self.btn_saveDatabase = self.findChild(QtWidgets.QPushButton, "btn_saveDatabase")
        self.btn_savePrinter = self.findChild(QtWidgets.QPushButton, "btn_savePrinter")
        self.btn_saveOtherSettings = self.findChild(QtWidgets.QPushButton, "btn_saveOtherSettings")
        self.btn_saveZpl = self.findChild(QtWidgets.QPushButton, "btn_saveZpl")
        self.btn_saveTpsl = self.findChild(QtWidgets.QPushButton, "btn_saveTpsl")

        self.btn_saveDatabase.clicked.connect(self.save_database)
        self.btn_savePrinter.clicked.connect(self.save_printer)
        self.btn_saveOtherSettings.clicked.connect(self.save_other_settings)
        self.btn_saveZpl.clicked.connect(self.save_zpl)
        self.btn_saveTpsl.clicked.connect(self.save_tpsl)

        self.cancelButton = self.findChild(QtWidgets.QPushButton, "btn_cancel")
        self.cancelButton.setCursor(Qt.PointingHandCursor)
        self.cancelButton.clicked.connect(self.close)
        self.saveButton = self.findChild(QtWidgets.QPushButton, "btn_save")
        self.saveButton.setCursor(Qt.PointingHandCursor)
        self.saveButton.clicked.connect(self.update_data)
        self.reloadButton = self.findChild(QtWidgets.QPushButton, "btn_reload")
        self.reloadButton.clicked.connect(self.reload_data)
        # Set the config path
        self.config_path = r'C:\barcode\barcode.json'

        # Load data from JSON file to UI elements
        self.load_data()

    def update_printer_in_json(self):
        current_data = self.printer_list.currentData()
        if current_data:  # Ensure data exists
            vid, pid, out_endpoints = current_data  # Unpack VID and PID
            self.printerVid.setText(hex(vid))  # Update UI
            self.printerPid.setText(hex(pid))
            self.endpoint.setText(out_endpoints[0])

    def save_database(self):
        try:
            # Read the current configuration file
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Update only the necessary keys
            config['server'] = self.serverName.text()
            config['database'] = self.databaseName.text()
            config['username'] = self.userName.text()
            config['password'] = self.password.text()

            # Write back the updated content (without overwriting the entire file)
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)  # Preserve structure
            
            print("Successfully updated!")
            QMessageBox.information(self, 'Success', "Updated Successfully!")
        
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def save_printer(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['vid'] = self.printerVid.text()
            config['pid'] = self.printerPid.text()
            config['endpoint'] = self.endpoint.text()
            config['ip_address'] = self.ip_address.text()
            config['wireless_mode'] = self.wireless_mode.isChecked()

            # Write back the updated configuration
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)
            
            print("Successfully updated!")
            QMessageBox.information(self, 'Success', "Updated Successfully!")
        
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def save_other_settings(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['companyName'] = self.companyName.text()
            config['location'] = self.location.text()
            config['logging'] = self.cb_logging.isChecked()  # Simplified conditional assignment

            # Write back the updated configuration
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            print("Successfully updated!")
            QMessageBox.information(self, 'Success', "Updated Successfully!")
        
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def save_zpl(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['zplTemplate'] = self.zplCommand.toPlainText()
            config['useZPL'] = self.use_zpl.isChecked()

            # Write back the updated configuration
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            print("Successfully updated!")
            QMessageBox.information(self, 'Success', "Updated Successfully!")
        
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def save_tpsl(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['tpslTemplate'] = self.tpslCommand.toPlainText()
            config['useZPL'] = self.use_zpl.isChecked()

            # Write back the updated configuration
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            print("Successfully updated!")
            QMessageBox.information(self, 'Success', "Updated Successfully!")
        
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def reload_data(self):
        self.load_data()
        self.populate_printer_list()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def populate_printer_list(self):
        self.printer_list.clear()  # Clear existing items
        printers = []  # To store detected printers

        # Find USB devices
        devices = find_usb(find_all=True, backend=self.backend)
        for device in devices:

            # Try to find the endpoints of the USB device
            endpoints = []
            try:
                for cfg in device:
                    if cfg.bDeviceClass == 7:
                        for intf in cfg:
                            for ep in intf:
                                if ep.bEndpointAddress:
                                    if ep.bEndpointAddress and (ep.bEndpointAddress & 0x80 == 0):  # OUT endpoints
                                        endpoint_info = hex(ep.bEndpointAddress)
                                        endpoints.append(endpoint_info)
            except Exception as e:
                print(f"Error reading endpoints for device {device}: {e}")

            product_name: str = ""
            # Add printer and its endpoint information to the list
            endpoint_info:int = ', '.join(endpoints) if endpoints else -1
            if self.supports_langids(device):  # Only proceed if langids are supported
                try:
                    # Safely fetch product name
                    product_name = device.product if device.product else "Unknown Product"
                except (usb.core.USBError, ValueError):
                    product_name = "Unknown Product"
            printer_info = f"{hex(device.idVendor)}:{hex(device.idProduct)} - {product_name} | {endpoint_info}"
            printers.append((device.idVendor, device.idProduct, endpoints, printer_info))

        # Add detected printers to the ComboBox
        for vid, pid, out_endpoints, info in printers:
            self.printer_list.addItem(info, userData=(vid, pid, out_endpoints))

        # Optionally, handle case where no printers are found
        if not printers:
            self.printer_list.addItem("No printers found", userData=None)

    def supports_langids(self, device):
        try:
            # Try to access langids
            langids = device.langids
            return True  # langids supported
        except (usb.core.USBError, NotImplementedError, ValueError):
            return False  # langids not supported


    def onWirelessModeStateChanged(self):
        if self.wireless_mode.isChecked():
            self.printerPid.setEnabled(False)
            self.printerVid.setEnabled(False)
            self.endpoint.setEnabled(False)
            self.ip_address.setEnabled(True)

        else:
            self.printerPid.setEnabled(True)
            self.printerVid.setEnabled(True)
            self.endpoint.setEnabled(True)
            self.ip_address.setEnabled(False)

    def onUseZPLStateChanged(self):
        if self.use_zpl.isChecked():
            self.tpslCommand.setEnabled(False)
            self.use_tpsl.setChecked(False)
            self.zplCommand.setEnabled(True)
        if self.use_tpsl.isChecked():
            self.zplCommand.setEnabled(False)
            self.use_zpl.setChecked(False)
            self.tpslCommand.setEnabled(True)
            self.use_tpsl.setChecked(True)

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
                self.ip_address.setText(config['ip_address'])
                if config['useZPL']:
                    self.use_tpsl.setChecked(False)
                    self.use_zpl.setChecked(True)
                else:
                    self.use_zpl.setChecked(False)
                    self.use_tpsl.setChecked(True)
                self.companyName.setText(config['companyName'])
                self.location.setText(config['location'])
                self.tpslCommand.setText(config['tpslTemplate'])
                self.zplCommand.setText(config['zplTemplate'])
                if config['wireless_mode']:
                    self.wireless_mode.setChecked(True)
                else:
                    self.wireless_mode.setChecked(False)

                if config['logging']:
                    self.cb_logging.setChecked(True)
                else:
                    self.cb_logging.setChecked(False)
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
            config['ip_address'] = self.ip_address.text()
            config['zplTemplate'] = self.zplCommand.toPlainText()
            config['tpslTemplate'] = self.tpslCommand.toPlainText()
            config['wireless_mode'] = self.wireless_mode.isChecked()
            config['useZPL'] = self.use_zpl.isChecked()

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())