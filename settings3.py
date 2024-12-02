import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QButtonGroup, QFileDialog
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import QtWidgets, uic
import usb.backend
import usb.backend.libusb1
import json
import usb
import os
from modules.logger_config import setup_logger
from version import __version__
from modules import CheckDriver, SendCommand, create_configurations, Configurations
from modules.InstallDriver import DriverInstaller

class SettingsWindow(QMainWindow):
    def __init__(self):
        super(SettingsWindow, self).__init__()
        self.logger = setup_logger('Settings2')  # Create logger specific to this window
        self.driverInstaller = DriverInstaller()
        self.backend = usb.backend.libusb1.get_backend(find_library=self.resource_path('libusb-1.0.ddl'))
        self.barcode_config = Configurations.BarcodeConfig()
        # Load the UI file first
        self.logger = setup_logger('Settings2')  # Create logger specific to this window
        uic.loadUi(self.resource_path("ui/settings3.ui"), self)
        self.logger.info("Settings2 initialized.")

        self.setWindowIcon(QIcon(self.resource_path("images/logo.ico")))
        self.setWindowTitle("Settings")
        #self.setFixedSize(1210, 696)

        # Alternatively, set the maximum size equal to the minimum size to prevent maximizing
        #self.setMaximumSize(1210, 696)
        self.setMinimumSize(1210, 696)

        self.logger.info("Initializing Widgets.")

        try:
            self.settings_icon = self.findChild(QtWidgets.QLabel, "settings_icon")
            settingsIcon = QPixmap(self.resource_path("images/setting.png"))
            databaseIcon = QPixmap(self.resource_path("images/database.png"))
            command = QPixmap(self.resource_path("images/command.png"))
            driver = QPixmap(self.resource_path("images/drivers.png"))
            printerIcon = QPixmap(self.resource_path("images/printer.png"))
            logoIcon = QPixmap(self.resource_path("images/logo.jpeg"))
            otherSettingsIcon = QPixmap(self.resource_path("images/settings.png"))
            zplIcon = QPixmap(self.resource_path("images/zpl.png"))
            tpslIcon = QPixmap(self.resource_path("images/tpsl.png"))
            self.settings_icon.setPixmap(settingsIcon)
            self.cb_logging = self.findChild(QtWidgets.QCheckBox, 'cb_logging')
            self.logger.info("Icons initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize icons: {e}")


        # Icons Section
        try:
            self.lbl_iconLogo = self.findChild(QtWidgets.QLabel, "lbl_iconLogo")
            self.lbl_iconLogo.setPixmap(logoIcon)
            self.lbl_driver = self.findChild(QtWidgets.QLabel, "lbl_iconDatabase_3")
            self.lbl_driver.setPixmap(driver)
            self.lbl_command = self.findChild(QtWidgets.QLabel, "lbl_customCommandIcon")
            self.lbl_command.setPixmap(command)
            self.lbl_version = self.findChild(QtWidgets.QLabel, "lbl_version")
            self.lbl_version.setText(f"Version {__version__}")
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
            self.logger.info("Successfully loaded icons")
        except Exception as e:
            self.logger.error(f"Failed to load icons: {e} ")

        # Access UI elements after loading the UI file
        try:
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
            self.wireless_mode = self.findChild(QtWidgets.QRadioButton, "rb_useIP")
            self.useGeneric = self.findChild(QtWidgets.QRadioButton, "rb_useGeneric")
            self.useCustom = self.findChild(QtWidgets.QRadioButton, "rb_useCustom")
            self.wireless_mode.toggled.connect(self.onWirelessModeStateChanged)
            self.useGeneric.toggled.connect(self.onWirelessModeStateChanged)
            self.useCustom.toggled.connect(self.onWirelessModeStateChanged)
            self.onWirelessModeStateChanged()
            self.companyName = self.findChild(QtWidgets.QLineEdit, "et_companyName")
            self.location = self.findChild(QtWidgets.QLineEdit, "et_location")
            self.tpslCommand = self.findChild(QtWidgets.QTextEdit, "et_tpslCommand")
            self.use_tpsl = self.findChild(QtWidgets.QRadioButton, "rb_tpsl")
            self.zplCommand = self.findChild(QtWidgets.QTextEdit, "et_zplCommand")
            self.use_zpl = self.findChild(QtWidgets.QRadioButton, "rb_zpl")
            self.use_zpl.toggled.connect(self.onUseZPLStateChanged)
            self.button_group = QButtonGroup()
            self.logger.error(f"Failed to initialize widgets for the dashboard")

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
            self.logger.info("Widgets initialized.")
            self.btn_sendCommand = self.findChild(QtWidgets.QPushButton, 'btn_sendCommand')
            self.btn_sendCommand.clicked.connect(self.send_command)
            self.btn_installdriver = self.findChild(QtWidgets.QPushButton, 'btn_DatabaseDriverInstall')
            self.btn_installdriver.clicked.connect(lambda: self.install_driver_from_ui("msodbcsql.msi"))
            self.btn_checkdriver = self.findChild(QtWidgets.QPushButton, 'btn_checkDatabaseDriver')
            self.btn_checkdriver.clicked.connect(self.set_database_driver_details)
        except Exception as e:
            self.logger.error(f"Failed to initialize widgets for the dashboard: {e}")

        # Set the config path
        self.logger.info("Initializing config path")

        self.config_path = r'C:\barcode\barcode.json'

        self.logger.info("Config path initialized.")

        # Load data from JSON file to UI elements
        try:
            self.load_data()
            self.logger.info("Successfully loaded data from json file to UI elements")
        except Exception as e:
            self.logger.error(f"Failed to load data from json file to UI elements: {e}")
        

    def update_printer_in_json(self):
        try:
            self.logger.info("Attempting to update printer information in the UI.")
            
            # Retrieve current data from the printer list
            current_data = self.printer_list.currentData()
            if not current_data:
                self.logger.warning("No printer data found in the current selection.")
                return

            # Unpack and update fields
            vid, pid, out_endpoints = current_data
            self.logger.debug(f"Printer data retrieved: VID={vid}, PID={pid}, Endpoints={out_endpoints}")
            
            self.printerVid.setText(str(vid))  # Update UI for VID
            self.logger.info(f"Printer VID updated to: {vid}")
            
            self.printerPid.setText(str(pid))  # Update UI for PID
            self.logger.info(f"Printer PID updated to: {pid}")
            
            if out_endpoints:
                self.endpoint.setText(str(out_endpoints[0]))  # Update UI for the first endpoint
                self.logger.info(f"Printer Endpoint updated to: {out_endpoints[0]}")
            else:
                self.logger.warning("No endpoints found for the selected printer.")
                self.endpoint.clear()
        except Exception as e:
            self.logger.error(f"Error while updating printer information: {e}")

    def save_database(self):
        try:
            self.logger.info("Starting database configuration save process.")
            
            # Read the current configuration file
            self.logger.debug(f"Reading configuration file from {self.config_path}.")
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Update only the necessary keys
            config['server'] = self.serverName.text()
            config['database'] = self.databaseName.text()
            config['username'] = self.userName.text()
            config['password'] = self.password.text()
            self.logger.debug("Updated database configuration keys: server, database, username, password.")
            
            # Write back the updated content (without overwriting the entire file)
            self.logger.debug(f"Writing updated configuration back to {self.config_path}.")
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)  # Preserve structure
            
            self.logger.info("Database configuration saved successfully.")
            QMessageBox.information(self, 'Success', "Database settings updated successfully!")
        
        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except Exception as e:
            error_message = f"Unexpected error occurred: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)

    def set_database_driver_details(self):
        """
        Populates the database driver details in the relevant UI fields.
        """
        try:
            # Locate the UI elements
            et_drivername = self.findChild(QtWidgets.QLineEdit, 'et_databaseDriverName')
            et_version = self.findChild(QtWidgets.QLineEdit, 'et_databaseVersion')
            et_driver = self.findChild(QtWidgets.QLineEdit, 'et_driverPath')
            et_setup = self.findChild(QtWidgets.QLineEdit, 'et_setupPath')
            self.et_generalCommand = self.findChild(QtWidgets.QLineEdit, 'et_generalCommand')

            if not all([et_drivername, et_version, et_driver, et_setup]):
                error_message = "One or more required UI elements are missing."
                self.logger.error(error_message)
                QMessageBox.critical(self, 'UI Error', error_message)
                return

            # Log initiation of ODBC driver check
            self.logger.info("Checking for ODBC driver details.")

            # Create an instance of BarcodeConfig
            barcode_config = Configurations.BarcodeConfig()

            # Retrieve the database driver name
            driver_name = barcode_config.get_database_driver_name()
            self.logger.debug(f"Retrieved database driver name: {driver_name}")

            # Check for the specific ODBC driver
            status, result = CheckDriver.CheckDrivers.check_odbc_driver(self, driver_name)
            self.logger.debug(f"ODBC driver check returned status: {status}, result: {result}")

            # If the driver exists, populate the fields
            if status:
                self.logger.info("ODBC Driver found. Populating fields.")
                et_drivername.setText(driver_name)
                et_version.setText(result.get('DriverODBCVer', 'N/A'))
                et_driver.setText(result.get('Driver', 'N/A'))
                et_setup.setText(result.get('Setup', 'N/A'))
            else:
                # Handle case where driver is not found
                self.logger.warning(f"ODBC Driver '{driver_name}' not found.")
                default_message = "Driver not found"
                et_drivername.setText(default_message)
                et_version.setText(default_message)
                et_driver.setText(default_message)
                et_setup.setText(default_message)
                QMessageBox.warning(self, 'Driver Not Found', f"ODBC Driver '{driver_name}' is not installed.")

        except KeyError as e:
            error_message = f"Missing expected key in ODBC driver details: {e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Data Error', error_message)

        except Exception as e:
            error_message = f"An unexpected error occurred while setting database driver details: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Unexpected Error', error_message)

    def install_driver_from_ui(self, driver_filename):
        """
        Installs a driver package from the 'drivers/' folder.
        :param driver_filename: Name of the driver file located in the 'drivers/' folder.
        """
        try:
            # Construct the full path to the driver file
            driver_path = self.resource_path("drivers/msodbcsql.msi")

            # Check if the driver file exists
            if not os.path.exists(driver_path):
                self.logger.error(f"Driver package not found at {driver_path}.")
                QMessageBox.critical(None, "File Not Found", f"Driver package not found: {driver_path}")
                return

            # Confirm the installation
            user_confirmation = QMessageBox.question(
                None,
                "Install Driver",
                f"Are you sure you want to install the driver package:\n{driver_filename}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if user_confirmation == QMessageBox.No:
                self.logger.info("Driver installation canceled by the user.")
                return

            # Log the start of the installation
            self.logger.info(f"Starting driver installation for package: {driver_path}")

            # Execute the driver installation
            success = self.driverInstaller.install_driver(driver_path)

            # Notify the user of the result
            if success:
                QMessageBox.information(None, "Installation Complete", "Driver installed successfully.")
                self.logger.info(f"Driver installed successfully from {driver_path}.")
            else:
                QMessageBox.critical(None, "Installation Failed", "Driver installation failed. Check logs for details.")
                self.logger.error(f"Driver installation failed for {driver_path}.")

        except Exception as e:
            self.logger.exception(f"Unexpected error during driver installation: {e}")
            QMessageBox.critical(None, "Unexpected Error", f"An error occurred: {e}")


    def send_command(self):
        try:
            self.logger.info("Initiating send command process.")

            # Validate general command input
            if not self.et_generalCommand or not self.et_generalCommand.toPlainText():
                error_message = "General command input is empty or not found."
                self.logger.error(error_message)
                QMessageBox.warning(self, 'Input Error', error_message)
                return

            general_command = self.et_generalCommand.toPlainText()
            self.logger.debug(f"General command to be sent: {general_command}")
            barcode_config = Configurations.BarcodeConfig()
            send_command = SendCommand.SendCommand()
            # Use generic driver (PyUSB)
            if barcode_config.get_use_generic_driver():
                self.logger.info("Using generic driver (PyUSB).")
                try:
                    vid = barcode_config.get_vid()
                    pid = barcode_config.get_pid()
                    endpoint = barcode_config.get_endpoint()

                    self.logger.debug(f"Attempting to send command via PyUSB with VID={vid}, PID={pid}, Endpoint={endpoint}.")
                    send_command.send_pyusb_command(vid=vid, pid=pid, endpoint=endpoint, command=general_command)
                    self.logger.info("Command sent successfully via PyUSB.")
                    QMessageBox.information(self, "Sent Successfully", "Command sent successfully!")
                except Exception as e:
                    error_message = f"Error while sending command via PyUSB: {e}"
                    self.logger.error(error_message)
                    QMessageBox.critical(self, 'Error', error_message)

            # Use custom driver (Win32Print)
            elif not barcode_config.get_use_generic_driver():
                self.logger.info("Using custom driver (Win32Print).")
                printer_name = barcode_config.get_printer_name()

                if send_command.get_win32_printer_status(printer_name):
                    try:
                        self.logger.debug(f"Sending command to printer: {printer_name}.")
                        send_command.send_win32print(printer_name, general_command)
                        self.logger.info(f"Command sent successfully to printer: {printer_name}.")
                        QMessageBox.information(self, "Sent Successfully", f"Command sent successfully to printer: {printer_name}!")
                    except Exception as e:
                        error_message = f"Error while sending command via Win32Print: {e}"
                        self.logger.error(error_message)
                        QMessageBox.critical(self, 'Error', error_message)
                else:
                    warning_message = f"Printer '{printer_name}' is offline or not available."
                    self.logger.warning(warning_message)
                    QMessageBox.warning(self, 'Printer Status', warning_message)

            else:
                # Fallback for unexpected conditions
                fallback_message = "Unable to determine driver type. Please check the configuration."
                self.logger.error(fallback_message)
                QMessageBox.critical(self, 'Error', fallback_message)

        except Exception as e:
            # Log unexpected errors
            error_message = f"Unexpected error occurred in send_command: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)

    def save_printer(self):
        try:
            self.logger.info("Starting printer configuration save process.")
            
            # Read the current configuration file
            self.logger.debug(f"Reading configuration file from {self.config_path}.")
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['vid'] = self.printerVid.text()
            config['pid'] = self.printerPid.text()
            config['endpoint'] = self.endpoint.text()
            config['ip_address'] = self.ip_address.text()
            config['wireless_mode'] = self.wireless_mode.isChecked()
            config['useGenericDriver'] = self.useGeneric.isChecked()
            config['printerName'] = self.printer_list.currentData()
            self.logger.debug(f"Updated printer configuration keys: vid, pid, endpoint, ip_address, wireless_mode, useGenericDriver.")

            # Write back the updated configuration
            self.logger.debug(f"Writing updated printer configuration back to {self.config_path}.")
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            self.logger.info("Printer configuration saved successfully.")
            QMessageBox.information(self, 'Success', "Printer settings updated successfully!")
        
        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except Exception as e:
            error_message = f"Unexpected error occurred: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)

    def save_other_settings(self):
        try:
            self.logger.info("Starting other settings save process.")

            # Read the current configuration file
            self.logger.debug(f"Reading configuration file from {self.config_path}.")
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['companyName'] = self.companyName.text()
            config['location'] = self.location.text()
            config['logging'] = self.cb_logging.isChecked()  # Simplified conditional assignment
            self.logger.debug(f"Updated other settings: companyName='{config['companyName']}', location='{config['location']}', logging={config['logging']}.")

            # Write back the updated configuration
            self.logger.debug(f"Writing updated settings back to {self.config_path}.")
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            self.logger.info("Other settings saved successfully.")
            QMessageBox.information(self, 'Success', "Other settings updated successfully!")
        
        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)
        
        except Exception as e:
            error_message = f"Unexpected error occurred: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)

    def save_zpl(self):
        try:
            self.logger.info("Starting ZPL settings save process.")

            # Read the current configuration file
            self.logger.debug(f"Reading configuration file from {self.config_path}.")
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['zplTemplate'] = self.zplCommand.toPlainText()
            config['useZPL'] = self.use_zpl.isChecked()
            self.logger.debug(f"Updated ZPL settings: zplTemplate='{config['zplTemplate'][:50]}...' (truncated for display), useZPL={config['useZPL']}.")

            # Write back the updated configuration
            self.logger.debug(f"Writing updated ZPL settings back to {self.config_path}.")
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            self.logger.info("ZPL settings saved successfully.")
            QMessageBox.information(self, 'Success', "ZPL settings updated successfully!")

        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except Exception as e:
            error_message = f"Unexpected error occurred: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)


    def save_tpsl(self):
        try:
            self.logger.info("Starting TPSL settings save process.")

            # Read the current configuration file
            self.logger.debug(f"Reading configuration file from {self.config_path}.")
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Update necessary keys
            config['tpslTemplate'] = self.tpslCommand.toPlainText()
            config['useZPL'] = self.use_zpl.isChecked()
            self.logger.debug(f"Updated TPSL settings: tpslTemplate='{config['tpslTemplate'][:50]}...' (truncated for display), useZPL={config['useZPL']}.")

            # Write back the updated configuration
            self.logger.debug(f"Writing updated TPSL settings back to {self.config_path}.")
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            self.logger.info("TPSL settings saved successfully.")
            QMessageBox.information(self, 'Success', "TPSL settings updated successfully!")

        except FileNotFoundError:
            error_message = f"Configuration file not found at {self.config_path}."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except json.JSONDecodeError:
            error_message = "Error parsing the configuration file."
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except KeyError as e:
            error_message = f"Missing key in configuration file: {e}"
            self.logger.error(error_message)
            QMessageBox.critical(self, 'Config Error', error_message)

        except Exception as e:
            error_message = f"Unexpected error occurred: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)

    def reload_data(self):
        try:
            self.logger.info("Reloading data.")

            # Reload configuration data
            self.logger.debug("Loading data from the configuration file.")
            self.load_data()

            # Reload printer list
            self.logger.debug("Refreshing the printer list.")
            self.populate_printer_list()

            self.logger.info("Data reloaded successfully.")

        except Exception as e:
            error_message = f"Error occurred while reloading data: {e}"
            self.logger.exception(error_message)
            QMessageBox.critical(self, 'Error', error_message)

    def resource_path(self, relative_path):
        try:
            # Attempt to get the PyInstaller base path
            self.logger.debug(f"Attempting to resolve resource path for: {relative_path}")
            base_path = sys._MEIPASS
            self.logger.debug(f"PyInstaller base path resolved: {base_path}")
        except AttributeError:
            # Fall back to the current working directory in development mode
            base_path = os.path.abspath(".")
            self.logger.debug(f"Development mode detected. Base path resolved to: {base_path}")
        except Exception as e:
            self.logger.exception(f"Unexpected error while resolving base path: {e}")
            raise

        # Construct the absolute path to the resource
        absolute_path = os.path.join(base_path, relative_path)
        self.logger.debug(f"Absolute resource path resolved: {absolute_path}")
        return absolute_path
    
    def populate_printer_list(self):
        self.logger.info("Starting to populate printer list.")
        self.printer_list.clear()  # Clear existing items
        printers = []  # To store detected printers

        try:
            # Find all USB devices
            self.logger.debug("Searching for USB devices.")
            devices = usb.core.find(find_all=True)

            for device in devices:
                is_printer = False  # Track if the device is identified as a printer
                endpoints = []

                # Check if the device class is 7 (Printer)
                if device.bDeviceClass == 7:
                    is_printer = True
                    self.logger.debug(f"Device {hex(device.idVendor)}:{hex(device.idProduct)} identified as a printer based on bDeviceClass.")

                # If not, check each configuration and interface for class 7
                else:
                    for config in device:
                        for interface in config:
                            if interface.bInterfaceClass == 7:
                                is_printer = True
                                self.logger.debug(f"Device {hex(device.idVendor)}:{hex(device.idProduct)} identified as a printer based on interface class.")
                                # Collect OUT endpoints (bEndpointAddress & 0x80 == 0)
                                for ep in interface:
                                    if ep.bEndpointAddress & 0x80 == 0:
                                        endpoints.append(hex(ep.bEndpointAddress))
                                break  # Found a printer, exit loop

                # If identified as a printer, gather information
                if is_printer:
                    try:
                        product_name = device.product if device.product else "Unknown Product"
                    except (usb.core.USBError, ValueError):
                        self.logger.warning(f"Could not fetch product name for device {hex(device.idVendor)}:{hex(device.idProduct)}.")
                        product_name = "Unknown Product"

                    vid = hex(device.idVendor)
                    pid = hex(device.idProduct)
                    endpoint_info = ', '.join(endpoints) if endpoints else "No OUT endpoints"
                    printer_info = f"{vid}:{pid} - {product_name} | {endpoint_info}"
                    self.logger.debug(f"Printer found: {printer_info}")
                    printers.append((vid, pid, endpoints, printer_info))

            # Add printers to the ComboBox
            for vid, pid, out_endpoints, info in printers:
                self.printer_list.addItem(info, userData=(vid, pid, out_endpoints))
                self.logger.debug(f"Added printer to ComboBox: {info}")

            # Handle case where no printers are found
            if not printers:
                self.logger.info("No printers found.")
                self.printer_list.addItem("No printers found", userData=None)

        except usb.core.USBError as e:
            self.logger.error(f"USB Error while detecting devices: {e}")
            self.printer_list.addItem("USB Error", userData=None)
        except Exception as e:
            self.logger.exception(f"Unexpected error occurred while populating printer list: {e}")
            self.printer_list.addItem("Error occurred", userData=None)

        self.logger.info("Finished populating printer list.")

    def supports_langids(self, device):
        try:
            self.logger.debug(f"Checking langids support for device {hex(device.idVendor)}:{hex(device.idProduct)}.")
            # Try to access langids
            langids = device.langids
            self.logger.info(f"Device {hex(device.idVendor)}:{hex(device.idProduct)} supports langids: {langids}.")
            return True  # langids supported
        except usb.core.USBError as e:
            self.logger.warning(f"USBError while accessing langids for device {hex(device.idVendor)}:{hex(device.idProduct)}: {e}")
            return False
        except NotImplementedError:
            self.logger.warning(f"Langids not implemented for device {hex(device.idVendor)}:{hex(device.idProduct)}.")
            return False
        except ValueError as e:
            self.logger.warning(f"ValueError while accessing langids for device {hex(device.idVendor)}:{hex(device.idProduct)}: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error while checking langids for device {hex(device.idVendor)}:{hex(device.idProduct)}: {e}")
            return False


    def onWirelessModeStateChanged(self):
        if self.wireless_mode.isChecked():
            self.logger.info("Wireless mode enabled. Disabling printer configuration fields and enabling IP address field.")
            self.printerPid.setEnabled(False)
            self.printerVid.setEnabled(False)
            self.endpoint.setEnabled(False)
            self.ip_address.setEnabled(True)
        else:
            self.logger.info("Wireless mode disabled. Enabling printer configuration fields and disabling IP address field.")
            self.printerPid.setEnabled(True)
            self.printerVid.setEnabled(True)
            self.endpoint.setEnabled(True)
            self.ip_address.setEnabled(False)
        if self.useGeneric.isChecked():
            self.populate_printer_list()
        if self.useCustom.isChecked():
            self.populate_customdriver_printer_list()

    def populate_customdriver_printer_list(self):
    # Create an instance of CheckDrivers
        checker = CheckDriver.CheckDrivers()
        
        # Get the printer details
        got_printers, printers = checker.check_printer_driver()
        
        # Populate the combobox
        self.printer_list.clear()  # Clear existing items
        if got_printers:
            for printer in printers:
                print(printer)  # Debugging (optional)
                self.printer_list.addItem(printer, userData=printer)
        else:
            self.printer_list.addItem("No Printer Found!")


    def onUseZPLStateChanged(self):
        if self.use_zpl.isChecked():
            self.logger.info("ZPL mode selected. Disabling TPSL command and enabling ZPL command.")
            self.tpslCommand.setEnabled(False)
            self.use_tpsl.setChecked(False)
            self.zplCommand.setEnabled(True)

        if self.use_tpsl.isChecked():
            self.logger.info("TPSL mode selected. Disabling ZPL command and enabling TPSL command.")
            self.zplCommand.setEnabled(False)
            self.use_zpl.setChecked(False)
            self.tpslCommand.setEnabled(True)
            self.use_tpsl.setChecked(True)

    def load_data(self):
        try:
            # Log the beginning of the load process
            self.logger.info("Loading configuration data from the config file.")
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.logger.info("Configuration file loaded successfully.")
                
                # Populate the UI with data from the configuration file
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
                    self.logger.info("ZPL mode selected based on config.")
                else:
                    self.use_zpl.setChecked(False)
                    self.use_tpsl.setChecked(True)
                    self.logger.info("TPSL mode selected based on config.")
                    
                self.companyName.setText(config['companyName'])
                self.location.setText(config['location'])
                self.tpslCommand.setText(config['tpslTemplate'])
                self.zplCommand.setText(config['zplTemplate'])
                
                if config['wireless_mode']:
                    self.wireless_mode.setChecked(True)
                    self.logger.info("Wireless mode enabled.")
                if config['useGenericDriver']:
                    self.useGeneric.setChecked(True)
                else:
                    self.useCustom.setChecked(True)

                if config['logging']:
                    self.cb_logging.setChecked(True)
                    self.logger.info("Logging is enabled.")
                else:
                    self.cb_logging.setChecked(False)
                    self.logger.info("Logging is disabled.")

        except FileNotFoundError:
            self.logger.error(f"Configuration file not found at {self.config_path}")
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')

        except json.JSONDecodeError:
            self.logger.error('Error parsing the configuration file.')
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')

        except KeyError as e:
            self.logger.error(f'Missing key in configuration file: {e}')
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')

    def update_data(self):
        try:
            # Log the start of the process
            self.logger.info("Updating configuration data.")

            # Read the current configuration file
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Log the data being updated
            self.logger.info("Updating fields in the configuration file.")

            # Update necessary keys from the UI inputs
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
            config['logging'] = self.cb_logging.isChecked()
            config['useGenericDriver'] = self.useGeneric.isChecked()

            # Write back the updated content (without overwriting the entire file)
            with open(self.config_path, 'w') as file:
                json.dump(config, file, indent=4)

            # Log successful update
            self.logger.info("Configuration file updated successfully.")
            QMessageBox.information(self, 'Success', "Updated Successfully!")
            self.close()

        except FileNotFoundError:
            self.logger.error(f"Configuration file not found at {self.config_path}")
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')

        except json.JSONDecodeError:
            self.logger.error('Error parsing the configuration file.')
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')

        except KeyError as e:
            self.logger.error(f'Missing key in configuration file: {e}')
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())