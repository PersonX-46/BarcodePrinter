import sys
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QGridLayout
from PyQt5.QtCore import Qt, QTimer 
import time

class BarcodeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.db_connected = False
        self.connection = None
        self.warning_shown = False
        self.connect_to_database()
        self.loadStylesheet()
        QTimer.singleShot(0, self.fetch_items)

    def initUI(self):
        self.setWindowTitle('Barcode Printer')
        self.setGeometry(200, 200, 1300, 600)

        grid_layout = QGridLayout()

        self.item_code_input = QLineEdit(self)
        self.item_code_input.setPlaceholderText('Enter Item Code')
        self.item_code_input.textChanged.connect(self.filter_items)
        grid_layout.addWidget(QLabel("Search:"), 0, 0)
        grid_layout.addWidget(self.item_code_input, 0, 1)

        self.item_table = QTableWidget(self)
        self.item_table.setColumnCount(5) 
        self.item_table.setHorizontalHeaderLabels(["Select", "Item Code", "Description", "Unit Price", "Number of Copies"])
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows) 
        self.item_table.setSelectionMode(QTableWidget.NoSelection)

        self.item_table.setStyleSheet("QTableWidget::item:selected { background: transparent; }")
        grid_layout.addWidget(self.item_table, 1, 0, 1, 2)

        self.print_button = QPushButton('Print Barcode', self)
        self.print_button.clicked.connect(self.print_barcode)
        grid_layout.addWidget(self.print_button, 2, 0, 1, 2, alignment=Qt.AlignCenter)

        self.setLayout(grid_layout)

    def loadStylesheet(self):
        """Load the stylesheet directly as a string."""
        stylesheet = """
        QLabel {
            font-size: 20px;
            font-weight: bold;
        }

        QLineEdit {
            font-size: 18px;
            padding: 8px;
            border: 1px solid #dfdfdf;
            border-radius: 8px;
        }

        QTableWidget {
            font-size: 16px;
            padding: 4px;
            border: 1px solid black;
        }

        QPushButton {
            background-color: #0004ff;
            color: white;
            width: 150px;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            font-size: 20px;
            margin: 10px;
            cursor: pointer;
        }

        QPushButton:hover {
            background-color: rgb(0, 106, 255);
        }

        QPushButton:pressed {
            background-color: #000099;
        }

        QHeaderView::section {
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }
        """
        self.setStyleSheet(stylesheet)

    def connect_to_database(self):
        try:
            self.connection = mysql.connector.connect(
                host='192.168.1.220',
                database='ztest',
                user='test',
                password='123',
                charset='utf8',
                connection_timeout=3
            )
            if self.connection.is_connected():
                self.db_connected = True
                print('Success: Connected to Database')
        except Error as e:
            print(f"Error connecting to database: {e}")

    def fetch_items(self):
        if not self.db_connected:
            QMessageBox.critical(self, 'Database Error', 'Database is not connected. Items will not be shown.')
            return

        try:
            cursor = self.connection.cursor()
            query = "SELECT ItemCode, Description, UnitPrice FROM stk_master"
            cursor.execute(query)
            items = cursor.fetchall()
            self.item_table.setRowCount(len(items))
            self.all_items = items  
            self.display_items(items)
        except Error as e:
            QMessageBox.critical(self, 'Database Error', f"Error fetching items: {e}")

    def display_items(self, items):
        self.item_table.setRowCount(len(items))
        for row_number, item in enumerate(items):

            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.item_table.setItem(row_number, 0, checkbox_item)

            for col_number, value in enumerate(item, start=1): 
                table_item = QTableWidgetItem(str(value))
                table_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                table_item.setTextAlignment(Qt.AlignCenter)  # Optional: Center text
                self.item_table.setItem(row_number, col_number, table_item)

            copies_item = QTableWidgetItem("1")
            copies_item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # Allow editing
            copies_item.setTextAlignment(Qt.AlignCenter)  # Center the text in the "Number of Copies" column
            self.item_table.setItem(row_number, 4, copies_item)

        self.item_table.resizeColumnsToContents()

        padding = 20  
        for column in range(self.item_table.columnCount()):
            current_width = self.item_table.columnWidth(column)
            self.item_table.setColumnWidth(column, current_width + padding)

    def filter_items(self):
        if not self.db_connected or not hasattr(self, 'all_items'):
            if not self.warning_shown:
                QMessageBox.warning(self, 'Database Error', 'Database is not connected. Searched items will not be shown.')
                self.warning_shown = True 
            return
    
        search_text = self.item_code_input.text().strip()
        filtered_items = [item for item in self.all_items if search_text.lower() in item[0].lower() or search_text in item[1].lower()]
        self.display_items(filtered_items)

    def print_barcode(self):
        selected_rows = []
        for row in range(self.item_table.rowCount()):
            if self.item_table.item(row, 0).checkState() == Qt.Checked:
                selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, 'Selection Error', 'No items selected for printing.')
            return

        try:
            timestamp = time.strftime("%Y%m%d_%H-%M-%S")
            filename = f'barcode_commands_{timestamp}.txt'

            with open(filename, 'w') as f:
                for row in selected_rows:
                    item_code = self.item_table.item(row, 1).text()
                    description = self.item_table.item(row, 2).text()
                    unit_price = self.item_table.item(row, 3).text()
                    copies = self.item_table.item(row, 4).text()

                    command = f"""SPEED 2.0
DENSITY 7
SET CUTTER OFF
SET PEEL OFF
DIRECTION 0
SIZE 35MM, 25MM
OFFSET 0.000
REFERENCE 0,0
CLS
TEXT 280,5,"3",0,1,1,"ALPHA DIGITAL (M) SDN BHD"
TEXT 280,40,"2",0,1,1,"{item_code}"
TEXT 280,120,"1",0,1,1,"{description}"
BARCODE 280,60,"128",50,0,0,2,1,"{item_code}"
TEXT 280,160,"4",0,1,1,"RM {unit_price}"
PRINT {copies},1
        """
                    f.write(command + "\n")

            QMessageBox.information(self, 'Success', f'Barcode commands saved to {filename} successfully.')
        except Exception as e:
            QMessageBox.critical(self, 'File Error', f"Error writing to file: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BarcodeApp()
    window.show()
    sys.exit(app.exec_())
