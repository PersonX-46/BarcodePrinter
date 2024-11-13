import sys
import pyodbc
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QGridLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QIcon
import usb
import usb.core
import usb.util
import usb.backend.libusb1
import json
from bisect import bisect_left

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
            self.items_fetched.emit(items)
        except pyodbc.Error as e:
            print(f"Error fetching items: {e}")



class BarcodeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.config_path = r'C:\barcode\barcode.json' 
        self.load_config() 
        self.backend = usb.backend.libusb1.get_backend(find_library='libusb-1.0.ddl')
        self.setWindowIcon(QIcon("icon.png"))
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
        except FileNotFoundError:
            QMessageBox.critical(self, 'Config Error', f'Configuration file not found at {self.config_path}')
            sys.exit(1)
        except json.JSONDecodeError:
            QMessageBox.critical(self, 'Config Error', 'Error parsing the configuration file.')
            sys.exit(1)
        except KeyError as e:
            QMessageBox.critical(self, 'Config Error', f'Missing key in configuration file: {e}')
            sys.exit(1)

    def initUI(self):
        self.setWindowTitle('Barcode Printer')
        self.setGeometry(200, 200, 1400, 600)

        # Main grid layout
        grid_layout = QGridLayout()

        # Horizontal layout for search bar and button
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.item_code_input = QLineEdit(self)
        self.item_code_input.setPlaceholderText('Enter Item Code')
        self.item_code_input.textChanged.connect(lambda: self.filter_items_binary(sortBy='barcode'))

        self.search_by_description = QPushButton("Search", self)
        self.search_by_description.clicked.connect(self.filter_items)

        # Add widgets to the horizontal search layout
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.item_code_input)
        search_layout.addWidget(self.search_by_description)

        # Add the search layout to the grid layout (entire top row)
        grid_layout.addLayout(search_layout, 0, 0, 1, 3)

        # Table widget spanning all columns in the second row
        self.item_table = QTableWidget(self)
        self.item_table.setColumnCount(9)
        self.item_table.setHorizontalHeaderLabels([
            "Select", "Item Code", "Description", "Unit Price", "Unit Cost", 
            "Barcode", "Location", "Location Price", "Number of Copies"
        ])
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setSelectionMode(QTableWidget.NoSelection)
        grid_layout.addWidget(self.item_table, 1, 0, 1, 3)  # Spanning all 3 columns

        # Print button centered in the bottom row
        self.print_button = QPushButton('Print Barcode', self)
        self.print_button.clicked.connect(self.print_barcode)
        grid_layout.addWidget(self.print_button, 2, 0, 1, 3, alignment=Qt.AlignCenter)


        # Set the main layout
        self.setLayout(grid_layout)

    def loadStylesheet(self):
        stylesheet = """
        QLabel { font-size: 20px; font-weight: bold; }
        QLineEdit { font-size: 18px; padding: 8px; border: 1px solid #dfdfdf; border-radius: 8px; }
        QTableWidget { font-size: 16px; padding: 4px; border: 1px solid black; }
        QPushButton {
            background-color: #0004ff; color: white; width: 150px; border: none;
            border-radius: 10px; padding: 10px 20px; font-size: 20px; margin: 10px; cursor: pointer;
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
    
    def display_items(self, items):
        self.item_table.setRowCount(len(items))
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Select column, smallest
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)           # Item Code
        self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)           # Description, largest
        self.item_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unit Price
        self.item_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Unit Cost
        self.item_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # Barcode
        self.item_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Location
        #self.item_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Location Price
        #self.item_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Number Of Copies


        # Set the proportions by manually adjusting the column widths after stretching
        self.item_table.setColumnWidth(0, 50)   # Select column, smallest
        self.item_table.setColumnWidth(1, 150)  # Item Code column, medium
        self.item_table.setColumnWidth(2, 300)  # Description column, largest
        self.item_table.setColumnWidth(3, 100)  # Unit Price column, smaller
        self.item_table.setColumnWidth(4, 150)  # Barcode column, medium
        self.item_table.setColumnWidth(5, 70)   # Copies column, smaller
        for row_number, item in enumerate(items):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.item_table.setItem(row_number, 0, checkbox_item)
            self.item_table.item(row_number, 0).setTextAlignment(Qt.AlignLeft)

            item_code, description, unit_price, unit_cost, barcode, location, location_price= item
            barcode_value = item_code if barcode is None else barcode  # Set barcode_value based on condition

            try:
                formatted_unit_price = f"RM {float(unit_price):.2f}" if unit_price is not None else "RM 0.00"
                formatted_unit_cost = f"RM {float(unit_cost):.2f}" if unit_cost is not None else "RM 0.00"
                formatted_location_price = f"RM {float(location_price):.2f}" if location_price is not None else "RM 0.00"

            except ValueError:
                formatted_unit_price = "0.00"
            for col_number, value in enumerate([item_code, description, formatted_unit_price , formatted_unit_cost, barcode_value , location, formatted_location_price ], start=1):
                table_item = QTableWidgetItem(str(value))
                table_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                table_item.setTextAlignment(Qt.AlignCenter)
                self.item_table.setItem(row_number, col_number, table_item)

            copies_item = QTableWidgetItem("1")
            copies_item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
            copies_item.setTextAlignment(Qt.AlignCenter)
            self.item_table.setItem(row_number, 8, copies_item)

        self.item_table.resizeColumnsToContents()

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

    def binary_search(self, items, target:str, sortBy:str='barcode'):

        if sortBy == 'description':
            item_codes = [str(item[1]).lower() for item in items]
        elif sortBy == 'barcode':
            item_codes = [str(item[4]).lower() for item in items]
        index = bisect_left(item_codes, target.lower())

        if index < len(item_codes) and item_codes[index] == target.lower():
            return items[index]
        return None

    def filter_items_binary(self, sortBy:str='barcode'):
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True
            return
        
        if sortBy == "description":
             self.all_items = sorted(self.items, key=lambda x: x[1].lower())
        elif sortBy == 'barcode':
            self.all_items = sorted(self.items, key=lambda x:x[4].lower() )

        search_text = self.item_code_input.text().strip().lower()

        if not search_text:
            self.display_items(self.all_items)
            return
        
        found_item = self.binary_search(self.all_items, search_text, sortBy=sortBy)
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
                if printer_clear:
                    print("contains data")
                if self.command_language.lower() == "tpsl":

                    printer_clear = "CLS"
                    barcode_data = f"""
    SPEED 2.0
    DENSITY 7
    DIRECTION 0
    SIZE 35MM, 25MM
    OFFSET 0.000
    REFERENCE 0,0
    CLS
    TEXT 320,5,"2",0,1,1,"{self.companyName}"
    TEXT 310,40,"2",0,1,1,"{barcode_value}"
    TEXT 310,120,"1",0,1,1,"{description}"
    BARCODE 300,60,"128",50,0,0,2,10,"{barcode_value}"
    TEXT 310,160,"4",0,1,1,"{unit_price_integer}"
    PRINT {copies}
    EOP
    """
                elif self.command_language.lower() == "zpl":
                    printer_clear = "^XA^CLS^XZ"
                    barcode_data = f"""
^XA
^LH0,-40
^PW889
^LL675
^FO320,-40^A0N,20,20^FD{self.companyName}^FS
^FO310,30^A0N,15,20^FD{description}^FS
^BY1,1,60  ; Fixed-width barcode command
^FO300,50^BCN,50,N,N,N^FD{barcode_value}^FS
^FO300,110^A0N,30,30^FD{unit_price_integer}^FS
^PQ{copies}
^XZ
    """
                # Send the barcode data to the printer
                print("data", barcode_data)
                printer.write(self.endpoint, barcode_data.encode('ascii'))
                print(f"Barcode print command sent successfully for item: {barcode_value}")

        except usb.core.USBError as e:
            QMessageBox.information(self, 'Error', f'{e}')
            print(f"USB Error: {e}")
        except ValueError as e:
            QMessageBox.information(self, 'Error', f'{e}')
            print(f'Value Error: {e}')
        finally:
            # Show success message once after all items are printed
            printer.write(self.endpoint, printer_clear.encode('ascii'))
            QMessageBox.information(self, 'Success', 'All selected items have been successfully sent to the printer!')
            usb.util.dispose_resources(printer)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BarcodeApp()
    window.showMaximized()
    sys.exit(app.exec_())