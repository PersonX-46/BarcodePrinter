import json
import os
from PyQt5.QtCore import QSettings, pyqtSignal, QObject

class BarcodeConfig(QObject):

    setting_changed = pyqtSignal(str, object)

    tpsl_template = ""
    tpsl_template80 = ""
    tpsl_template3 = ""

    zpl_template = ""
    zpl_template80 = ""
    zpl_template3 = ""


    def __init__(self):
        super().__init__()
        self.settings = QSettings("AlphaDigital", "BarcodePrinter")
        self.json_path = "C:/barcode/barcode.json"

    # Getters and Setters
    def get_server(self):
        return self.settings.value("server", "localhost")

    def set_server(self, server):
        self.settings.setValue("server", server)
        self.setting_changed.emit("server", server)

    def get_database(self):
        return self.settings.value("database", "example_db")

    def set_database(self, database):
        self.settings.setValue("database", database)
        self.setting_changed.emit("database", database)

    def get_username(self):
        return self.settings.value("username", "admin")

    def set_username(self, username):
        self.settings.setValue("username", username)
        self.setting_changed.emit("username", username)

    def get_password(self):
        return self.settings.value("password", "admin123")

    def set_password(self, password):
        self.settings.setValue("password", password)
        self.setting_changed.emit("password", password)

    def get_vid(self):
        return self.settings.value("vid", "0x1234")

    def set_vid(self, vid):
        self.settings.setValue("vid", vid)
        self.setting_changed.emit("vid", vid)

    def get_pid(self):
        return self.settings.value("pid", "0x5678")

    def set_pid(self, pid):
        self.settings.setValue("pid", pid)
        self.setting_changed.emit("pid", pid)

    def get_endpoint(self):
        return self.settings.value("endpoint", "0x01")

    def set_endpoint(self, endpoint):
        self.settings.setValue("endpoint", endpoint)
        self.setting_changed.emit("endpoint", endpoint)

    def get_company_name(self):
        return self.settings.value("companyName", "Example Corp")

    def set_company_name(self, company_name):
        self.settings.setValue("companyName", company_name)
        self.setting_changed.emit("companyName", company_name)

    def get_location(self):
        return self.settings.value("location", "HQ")

    def set_location(self, location):
        self.settings.setValue("location", location)
        self.setting_changed.emit("location", location)

    def get_use_zpl(self):
        return self.settings.value("useZPL", True, type=bool)

    def set_use_zpl(self, use_zpl):
        self.settings.setValue("useZPL", use_zpl)
        self.setting_changed.emit("useZPL", use_zpl)

    def get_ip_address(self):
        return self.settings.value("ip_address", "192.168.1.100")

    def set_ip_address(self, ip_address):
        self.settings.setValue("ip_address", ip_address)
        self.setting_changed.emit("ip_address", ip_address)

    def get_wireless_mode(self):
        return self.settings.value("wireless_mode", False, type=bool)

    def set_wireless_mode(self, wireless_mode):
        self.settings.setValue("wireless_mode", wireless_mode)
        self.setting_changed.emit("wireless_mode", wireless_mode)

    def get_zpl_template(self):
        return self.settings.value("zplTemplate", "")

    def set_zpl_template(self, zpl_template):
        self.settings.setValue("zplTemplate", zpl_template)
        self.setting_changed.emit("zplTemplate", zpl_template)

    def get_tpsl_template(self):
        return self.settings.value("tpslTemplate", "")

    def set_tpsl_template(self, tpsl_template):
        self.settings.setValue("tpslTemplate", tpsl_template)
        self.setting_changed.emit("tpslTemplate", tpsl_template)

    def get_tpsl_size80_template(self):
        return self.settings.value("tpsl2")
    
    def set_tpsl_size80_template(self, tpsl80_template):
        self.settings.setValue("tpsl2", tpsl80_template)
        self.setting_changed.emit("tpsl2", tpsl80_template)

    def get_zpl_size80_template(self):
        return self.settings.value("zpl2")
    
    def set_zpl_size80_template(self, zpl80_template):
        self.settings.setValue("zpl2", zpl80_template)
        self.setting_changed.emit("zpl2", zpl80_template)
    
    def get_tpsl_size3_template(self):
        return self.settings.value("tpsl3")
    
    def set_tpsl_size3_template(self, tpsl3_template):
        self.settings.setValue("tpsl3", tpsl3_template)
        self.setting_changed.emit("tpsl3", tpsl3_template)

    def get_zpl_size3_template(self):
        return self.settings.value("zpl3")
    
    def set_zpl_size3_template(self, zpl3_template):
        self.settings.setValue("zpl3", zpl3_template)
        self.setting_changed.emit("zpl3", zpl3_template)

    def get_logging(self):
        return self.settings.value("logging", True, type=bool)

    def set_logging(self, logging):
        self.settings.setValue("logging", logging)
        self.setting_changed.emit("logging", logging)

    def get_item_count(self):
        return self.settings.value("itemCount", 100, type=int)

    def set_item_count(self, item_count):
        self.settings.setValue("itemCount", item_count)
        self.setting_changed.emit("itemCount", item_count)

    def get_enter_to_search(self):
        return self.settings.value("enterToSearch", True, type=bool)

    def set_enter_to_search(self, enter_to_search):
        self.settings.setValue("enterToSearch", enter_to_search)
        self.setting_changed.emit("enterToSearch", enter_to_search)

    def get_use_generic_driver(self):
        return self.settings.value("useGenericDriver", True, type=bool)

    def set_use_generic_driver(self, use_generic_driver):
        self.settings.setValue("useGenericDriver", use_generic_driver)
        self.setting_changed.emit("useGenericDriver", use_generic_driver)

    def get_printer_name(self):
        return self.settings.value("printerName", "TSC_TA200")

    def set_printer_name(self, printer_name):
        self.settings.setValue("printerName", printer_name)
        self.setting_changed.emit("printerName", printer_name)

    def get_database_driver_name(self):
        return self.settings.value("databaseDriverName", "ODBC Driver 18 for SQL Server")

    def set_database_driver_name(self, database_driver_name):
        self.settings.setValue("databaseDriverName", database_driver_name)
        self.setting_changed.emit("databaseDriverName", database_driver_name)

    def get_hide_cost(self):
        return self.settings.value("hideCost", False, type=bool)

    def set_hide_cost(self, hide_cost):
        self.settings.setValue("hideCost", hide_cost)
        self.setting_changed.emit("hideCost", hide_cost)
    
    def get_trusted_connection(self):
        return self.settings.value("trustedConnection", False, type=bool)
    
    def set_trusted_connection(self, trusted_connection):
        self.settings.setValue("trustedConnection", trusted_connection)
        self.setting_changed.emit("trustedConnection", trusted_connection)

    def get_tpslSize(self):
        return self.settings.value("tpslSize", False, type=str)

    def set_tpslSize(self, tpslSize):
        self.settings.setValue("tpslSize", tpslSize)
        self.setting_changed.emit("tpslSize", tpslSize)
    
    def get_zplSize(self):
        return self.settings.value("zplSize", False, type=str)
    
    def set_zplSize(self, tpslSize:str):
        self.settings.setValue("zplSize", tpslSize)
    
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        # defaults = {
        #     "server": "localhost",
        #     "database": "example_db",
        #     "username": "admin",
        #     "password": "admin123",
        #     "vid": "0x1234",
        #     "pid": "0x5678",
        #     "endpoint": "0x01",
        #     "companyName": "Example Corp",
        #     "location": "HQ",
        #     "useZPL": True,
        #     "ip_address": "192.168.1.100",
        #     "wireless_mode": False,
        #     "zplTemplate": "^XA \n^LH0,-7\n^C128\n^PR3\n^PW280 \n^FO10,0,^A0N,20,20^FD{{companyName}}^FS ^FO10,25^A0N,15,20^FD{{barcode_value}}^FS ^FO10,40^BY1,1.5,0^BCN,50,N,Y,N,N^FD{{barcode_value}}^FS \n^A0N,50,50\n^FO10,94^A0N,15,20^FB280,3,0,L,0 ^FD{{description}}^FS ^FO10,130^A0N,25,30^FD{{unit_price_integer}}^FS \n^PQ{{copies}} \n^XZ",
        #     "tpslTemplate": "SPEED 2.0 \nDENSITY 7 \nDIRECTION 0 \nSIZE 35MM,25MM \nOFFSET 0.000 \nREFERENCE 0,0 \nCLS \nTEXT 320,5,\"2\",0,1,1,\"{{companyName}}\" \nTEXT 310,40,\"2\",0,1,1,\"{{barcode_value}}\" \nTEXT 310,120,\"0\",0,1,1,\"{{description}}\" \nBARCODE 310,60,\"128\",50,0,0,2,10,\"{{barcode_value}}\" \nTEXT 310,160,\"4\",0,1,1,\"{{unit_price_integer}}\" \nPRINT {{copies}} \nEOP",
        #     "logging": True,
        #     "itemCount": 100,
        #     "enterToSearch": True,
        #     "useGenericDriver": True,
        #     "printerName": "TSC_TA200",
        #     "databaseDriverName": "ODBC Driver 18 for SQL Server",
        #     "hideCost": False,
        # }

        """Reset all settings to their default values from the JSON file."""
        if not os.path.exists(self.json_path):
            print(f"Error: JSON file not found at {self.json_path}")
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                defaults = json.load(file)

            for key, value in defaults.items():
                self.settings.setValue(key, value)
                self.setting_changed.emit(key, value)  # Emit signal for UI updates if needed

            print("Settings reset to defaults from JSON file.")

        except Exception as e:
            print(f"Error reading JSON file: {e}")

        


# Example usage:
if __name__ == "__main__":
    config = BarcodeConfig()

    # Get some values
    print(config.get_server())  # Get the server
    print(config.get_database())  # Get the database

    # Set some values
    config.set_server("new_server")
    config.set_database("new_database")
