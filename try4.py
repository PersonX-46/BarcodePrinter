import os
import re
import sys
import pyodbc
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QGridLayout, QHBoxLayout, QVBoxLayout, QMenuBar, QAction, QMainWindow
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QFileSystemWatcher
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QIcon, QBrush, QColor
import usb
import usb.core
import usb.util
import usb.backend.libusb1
import json
from bisect import bisect_left
from settings import SettingsWindow

class FilterItemsBinaryThread(QThread):
    items_filtered = pyqtSignal(list)  # Signal to emit filtered items

    def __init__(self, all_items, search_text, sort_by='barcode'):
        super().__init__()
        self.all_items = all_items
        self.search_text = search_text.lower()
        self.sort_by = sort_by

    def binary_search(self, items, target: str):
        """Perform binary search for the target on pre-sorted items."""
        if self.sort_by == 'description':
            item_codes = [str(item[1]).lower() for item in items]
        elif self.sort_by == 'barcode':
            item_codes = [str(item[4]).lower() for item in items]

        index = bisect_left(item_codes, target)

        if index < len(item_codes) and item_codes[index] == target:
            return [items[index]]  # Return found item as a single-item list for uniform display
        return []

    def run(self):
        # Sort items before binary search
        if self.sort_by == "description":
            sorted_items = sorted(self.all_items, key=lambda x: x[1].lower())
        elif self.sort_by == 'barcode':
            sorted_items = sorted(self.all_items, key=lambda x: x[4].lower())

        # Apply binary search if there is search text; otherwise return all items
        if self.search_text:
            filtered_items = self.binary_search(sorted_items, self.search_text)
        else:
            filtered_items = sorted_items

        # Emit the filtered items
        self.items_filtered.emit(filtered_items)

class FetchItemsThread(QThread):
    items_fetched = pyqtSignal(list)

    def __init__(self, connection, location):
        super().__init__()
        self.connection = connection
        self.location = location

    def run(self):
        try:
            cursor = self.connection.cursor()
            query = f"""
            WITH BaseItems AS (
                SELECT
                    u.ItemCode,
                    i.Description,
                    u.Price AS DefaultUnitPrice,
                    u.Cost,
                    ISNULL(u.Barcode, i.ItemCode) as Barcode,
                    ISNULL(p.Location, 'HQ') as Location,
                    ISNULL(p.Price, u.Price) AS PosUnitPrice
                FROM dbo.ItemUOM u
                LEFT JOIN dbo.Item i ON u.ItemCode = i.ItemCode
                LEFT JOIN dbo.PosPricePlan p ON u.ItemCode = p.ItemCode AND p.Location = '{self.location}'
            )
            SELECT * FROM BaseItems;
            """
            cursor.execute(query)
            items = cursor.fetchall()
            self.all_items = sorted(items, key=lambda x:x[4].lower() )
            self.items_fetched.emit(self.all_items)
        except pyodbc.Error as e:
            print(f"Error fetching items: {e}")



class BarcodeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.config_path = r'C:\barcode\barcode.json'
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.addPath(self.config_path)
        self.file_watcher.fileChanged.connect(self.handle_config_change)
        self.load_config()
        self.backend = usb.backend.libusb1.get_backend(find_library='libusb-1.0.ddl')
        self.setWindowIcon(QIcon(self.resource_path(("logo.ico"))))
        self.db_connected = False
        self.connection = None
        self.warning_shown = False
        self.connect_to_database()
        self.loadStylesheet()
        self.showMaximized()
        self.fetch_items_thread = None
        self.items = []

        # Start fetching items on a separate thread
        self.start_fetch_items()

    def handle_config_change(self):
        """
        Handle changes in the JSON config file.
        """
        print("Configuration file changed. Reloading...")
        try:
            self.load_config()  # Reload configuration
            if self.db_connected:
                self.connection.close()
            self.connect_to_database()  # Reconnect to the database
            self.start_fetch_items()   # Refresh items
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to reload configuration: {e}")

    
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.server = config['server']
                self.database = config['database']
                self.username = config['username']
                self.password = config['password']
                self.vid = int(config['vid'], 16)
                self.pid = int(config['pid'], 16)
                self.endpoint = int(config['endpoint'], 16)
                self.companyName = config['companyName']
                self.location = config.get('location')
                self.command_language:str = config['commandLanguage']
                self.zpl_template:str = config['zplTemplate']
                self.tpsl_template:str = config['tpslTemplate']
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)


    def initUI(self):
        # Set the window properties
        self.setWindowTitle('Barcode Printer')
        self.setGeometry(200, 200, 1400, 600)
        self.setWindowIcon(QIcon(self.resource_path("logo.ico")))

        # Create a central widget to hold the main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)  # Set central widget

        # Main layout for the widget
        grid_layout = QGridLayout(central_widget)

        # === Menu Bar Section ===
        menu_bar = self.menuBar()  # Use QMainWindow's menuBar method
        file_menu = menu_bar.addMenu('Settings')
        settings_action = QAction('Open Settings', self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)


        # === Search Bar Section ===
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.item_code_input = QLineEdit(self)
        self.item_code_input.setPlaceholderText('Enter Item Code')
        self.item_code_input.textChanged.connect(self.filter_items_binary)

        # Search button
        self.search_by_description = QPushButton("Search", self)
        self.search_by_description.setCursor(Qt.PointingHandCursor)
        self.search_by_description.setStyleSheet("""
        QPushButton {
            background: qlineargradient(spread:pad, x1:0.148, y1:1, x2:1, y2:1, stop:0.233503 rgba(53, 132, 228, 255), stop:1 rgba(26, 95, 180, 255));
            color: white;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            font-style: italic;
            font-weight: bold;
            qproperty-cursor: pointingHandCursor;
        }
        QPushButton:hover {
            background: white;
            border: 2px solid rgb(53, 132, 228);
            color: black;
        }
        """)
        self.search_by_description.clicked.connect(self.filter_items)

        # Add widgets to the search layout
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.item_code_input)
        search_layout.addWidget(self.search_by_description)

        # Add search layout to the grid layout
        grid_layout.addLayout(search_layout, 0, 0, 1, 3)

        # === Item Table Section ===
        self.item_table = QTableWidget(self)
        self.item_table.setColumnCount(9)
        self.item_table.setHorizontalHeaderLabels([
            "Select", "Item Code", "Description", "Unit Price", "Unit Cost",
            "Barcode", "Location", "Location Price", "Number of Copies"
        ])
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setSelectionMode(QTableWidget.NoSelection)

        # Add table to the grid layout
        grid_layout.addWidget(self.item_table, 1, 0, 1, 3)

        # === Buttons Section ===
        print_layout = QHBoxLayout()

        # Print Button
        self.print_button = QPushButton('Print Barcode', self)
        self.print_button.setStyleSheet("""
        QPushButton {
            background: white;
            border: 2px solid rgb(53, 132, 228);
            color: black;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 8px;
            font-style: italic;
            font-weight: bold;
            qproperty-cursor: pointingHandCursor;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0.148, y1:1, x2:1, y2:1, stop:0.233503 rgba(53, 132, 228, 255), stop:1 rgba(26, 95, 180, 255));
            color: white;
        }
        """)
        self.print_button.setCursor(Qt.PointingHandCursor)
        self.print_button.clicked.connect(self.print_barcode)

        # Add buttons to the print layout
        print_layout.addWidget(self.print_button)

        # Add print layout to the grid layout
        grid_layout.addLayout(print_layout, 2, 0, 1, 3, alignment=Qt.AlignCenter)

    def loadStylesheet(self):
        stylesheet = """
        QLabel { font-size: 20px; font-weight: bold; }
        QLineEdit { font-size: 18px; padding: 8px; 	border: 2px solid rgb(53, 132, 228);border-radius: 10px;
    }
        QTableWidget { font-size: 16px; padding: 4px; border: 1px solid black; }
        QPushButton {
           padding: 10px 20px; font-size: 20px; margin: 10px;
        }
        QPushButton:hover { background-color: rgb(0, 106, 255); }
        QPushButton:pressed { background-color: #000099; }
        QHeaderView::section { font-size: 16px; font-weight: bold; padding: 10px; }
        """
        self.setStyleSheet(stylesheet)

    def connect_to_database(self):
        try:
            self.connection = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}'
            )
            if self.connection:
                self.db_connected = True
                print('Success: Connected to Database')
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")

    def replace_placeholders(self, template, **kwargs):
        return re.sub(r'{{(.*?)}}', lambda match: str(kwargs.get(match.group(1), match.group(0))), template)

    def start_fetch_items(self):
        if not self.db_connected:
            QMessageBox.critical(self, 'Database Error', 'Database is not connected. Items will not be shown.')
            return
        self.fetch_items_thread = FetchItemsThread(self.connection, self.location)
        self.fetch_items_thread.items_fetched.connect(self.handle_items_fetched)
        self.fetch_items_thread.start()

    def handle_items_fetched(self, items):
        self.items = items
        self.all_items = sorted(self.items, key=lambda x: x[4].lower())
        self.display_items(self.items)

    def open_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()
    
    def display_items(self, items):
        
        self.item_table.setRowCount(len(items[:100]))

        # Set column resize modes for headers
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Select column
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)           # Item Code
        self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)           # Description
        self.item_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unit Price
        self.item_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Unit Cost
        self.item_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)           # Barcode
        self.item_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Location

        # Manually adjust column widths after applying resize modes for more control
        self.item_table.setColumnWidth(0, 50)   # Select column, smallest
        self.item_table.setColumnWidth(1, 150)  # Item Code column, medium
        self.item_table.setColumnWidth(2, 300)  # Description column, largest
        self.item_table.setColumnWidth(3, 100)  # Unit Price column
        self.item_table.setColumnWidth(4, 150)  # Unit Cost column
        self.item_table.setColumnWidth(5, 100)  # Barcode column, adjusted for consistency
        self.item_table.setColumnWidth(6, 100)  # Location column

        # Add rows of items to the table
        for row_number, item in enumerate(items[:100]):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.item_table.setItem(row_number, 0, checkbox_item)
            self.item_table.item(row_number, 0).setTextAlignment(Qt.AlignLeft)

            # Extract item details
            item_code, description, unit_price, unit_cost, barcode, location, location_price = item
            barcode_value = item_code if barcode is None else barcode  # Fallback to item_code if barcode is None

            try:
                # Format currency values
                formatted_unit_price = f"RM {float(unit_price):.2f}" if unit_price is not None else "RM 0.00"
                formatted_unit_cost = f"RM {float(unit_cost):.2f}" if unit_cost is not None else "RM 0.00"
                formatted_location_price = f"RM {float(location_price):.2f}" if location_price is not None else "RM 0.00"
            except ValueError:
                formatted_unit_price = "RM 0.00"

            # Set the data for each row
            for col_number, value in enumerate([item_code, description, formatted_unit_price, formatted_unit_cost, barcode_value, location, formatted_location_price], start=1):
                table_item = QTableWidgetItem(str(value))
                table_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                table_item.setTextAlignment(Qt.AlignCenter)
                self.item_table.setItem(row_number, col_number, table_item)

            # Add copies column (editable)
            copies_item = QTableWidgetItem("1")
            copies_item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
            copies_item.setTextAlignment(Qt.AlignCenter)
            self.item_table.setItem(row_number, 8, copies_item)

            # Set background color for every even row (index 0, 2, 4, etc.)
            if row_number % 2 == 0:
                for col_number in range(self.item_table.columnCount()):
                    item = self.item_table.item(row_number, col_number)
                    item.setBackground(QBrush(QColor(230, 238, 255)))  # Set light gray background color for even rows

        # Adjust column sizes after filling in data
        self.item_table.resizeColumnsToContents()

        # Add padding to each column
        padding = 20
        for column in range(self.item_table.columnCount()):
            current_width = self.item_table.columnWidth(column)
            self.item_table.setColumnWidth(column, current_width + padding)


    def start_filter_items_thread(self):
        # Ensure database is connected
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True
            return

        # Get the current text and selected sortBy option
        search_text = self.item_code_input.text().strip().lower()
        sort_by = 'barcode' 

        # Terminate any running thread to prevent overlap
        if hasattr(self, 'filter_items_thread') and self.filter_items_thread.isRunning():
            self.filter_items_thread.terminate()

        # Start a new thread for filtering items
        self.filter_items_thread = FilterItemsBinaryThread(self.all_items, search_text, sort_by)
        self.filter_items_thread.items_filtered.connect(self.display_items)
        self.filter_items_thread.start()

    def binary_search(self, items, target:str):

        item_codes = [str(item[4]).lower() for item in items]
        index = bisect_left(item_codes, target.lower())

        if index < len(item_codes) and item_codes[index] == target.lower():
            return items[index]
        return None

    def filter_items_binary(self):
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True
            return  
        search_text = self.item_code_input.text().strip().lower()

        if not search_text:
            self.display_items(self.all_items[:100])
            return
        
        found_item = self.binary_search(self.all_items, search_text)
        if found_item:
            self.display_items([found_item])
        else:
            self.display_items([])
            #QMessageBox.information(self, "Item Not Found", 'No items match the search criteria!')

    def filter_items(self):
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True
            return

        search_text = self.item_code_input.text().strip().lower()
        keywords = search_text.split()  # Split the search text by spaces to create a list of keywords

    # Filter items if both ItemCode and Description contain each keyword in some order
        filtered_items = [
        item for item in self.all_items
            if all(
                keyword in item[1].lower()
                for keyword in keywords
            )
        ]  
        self.display_items(filtered_items)

    def print_barcode(self):
        selected_rows = []
        for row in range(self.item_table.rowCount()):
            if self.item_table.item(row, 0).checkState() == Qt.Checked:
                selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, 'Selection Error', 'No items selected for printing.')
            return

        # Set up the printer connection once, outside the loop
        printer = usb.core.find(idVendor=self.vid, idProduct=self.pid, backend=self.backend)

        if printer is None:
            QMessageBox.warning(self, 'Printer Error', 'Printer not found. Check your device and USB permissions.')
            return
        printer.set_configuration()

        try:
            # Loop through each selected item and send the print command
            for row in selected_rows:
                description = self.item_table.item(row, 2).text()
                unit_price_integer = self.item_table.item(row, 7).text()
                barcode_value = self.item_table.item(row, 5).text()  # Get barcode value
                copies = self.item_table.item(row, 8).text()

                printer_clear = ""
                barcode_data = ""
                if self.command_language.lower() == "tpsl":
                    print_data = self.replace_placeholders(self.tpsl_template, companyName=self.companyName, description=description, barcode_value = barcode_value, unit_price_integer=unit_price_integer, copies=copies)
                    printer_clear = "CLS"
                elif self.command_language.lower() == "zpl":
                    printer_clear = "^XA^CLS^XZ"
                    print_data = self.replace_placeholders(self.zpl_template, companyName=self.companyName, description=description, barcode_value = barcode_value, unit_price_integer=unit_price_integer, copies=copies)
                # Send the barcode data to the printer
                printer.write(self.endpoint, print_data.encode('utf-8'))
                print(f"Barcode print command sent successfully for item: {barcode_value}")

        except usb.core.USBError as e:
            QMessageBox.information(self, 'Error', f'{e}')
            print(f"USB Error: {e}")
        except ValueError as e:
            QMessageBox.information(self, 'Error', f'{e}')
            print(f'Value Error: {e}')
        finally:
            # Show success message once after all items are printed
            printer.write(self.endpoint, printer_clear.encode('utf-8'))
            QMessageBox.information(self, 'Success', 'All selected items have been successfully sent to the printer!')
            usb.util.dispose_resources(printer)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BarcodeApp()
    window.showMaximized()
    sys.exit(app.exec_())