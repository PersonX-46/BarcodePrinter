# import usb.core
# import usb.util

# VENDOR_ID = 0x20d1
# PRODUCT_ID = 0x7007  

# printer = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

# if printer is None:
#     raise ValueError("Printer not found. Check your device and USB permissions.")

# if printer.is_kernel_driver_active(0):
#     printer.detach_kernel_driver(0)

# printer.set_configuration()

# barcode_data = """
# SPEED 2.0
# DENSITY 7
# SET CUTTER OFF
# SET PEEL OFF
# DIRECTION 0
# SIZE 35MM, 25MM
# OFFSET 0.000
# REFERENCE 0,0
# CLS
# TEXT 320,5,"2",0,1,1,"ALPHA DIGITAL"
# TEXT 310,40,"2",0,1,1,"APPLE IPHONE 5"
# TEXT 310,120,"1",0,1,1,"APPLE IPHONE 5"
# BARCODE 300,60,"128",50,0,0,2,10,"APPLEIPHONE5"
# TEXT 310,160,"4",0,1,1,"RM 0"
# PRINT 1,1
# """

# try:
#     printer.write(1, barcode_data.encode('ascii')) 
#     print("Barcode print command sent successfully!")
# except usb.core.USBError as e:
#     print(f"Error: {e}")
# finally:
#     usb.util.dispose_resources(printer)


import usb.core
import usb.util

# Define Vendor and Product ID for the printer
VENDOR_ID = 0x20d1
PRODUCT_ID = 0x7007

# Find the printer
printer = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

# Check if the printer is connected
if printer is None:
    raise ValueError("Printer not found. Check your device and USB permissions.")

# Detach kernel driver if necessary
if printer.is_kernel_driver_active(0):
    printer.detach_kernel_driver(0)

# Set the printer configuration
printer.set_configuration()

# Clear the printer's memory before sending new data (like ^CLS in ZPL)
clear_buffer = "^XA^CLS^XZ"

# ZPL command for a simple label
zpl_data = f"""
^XA
^PR3
^PW280
^FO10,0,^A0N,20,20^FDCompany Name^FS
^FO10,25^A0N,15,20^955670105139^FS
^FO10,40^BY1,1,150^BCN,50,Y,Y,N,N^FD>: ABC6701@05139^FS
^FO10,94^A0N,15,20^FD100 PLUS BOX^FS
^FO10,120^A0N,30,30^FDRM100^FS
^PQ1
^XZ
"""

m = """
SPEED 2.0
DENSITY 7
DIRECTION 0
SIZE 35MM, 25MM
OFFSET 0.000
REFERENCE 0,0
CLS
TEXT 320,5,"2",0,1,1,"company name"
TEXT 310,40,"2",0,1,1,"ABC670105139"
TEXT 310,120,"1",0,1,1,"description"
BARCODE 305,60,"128",50,0,0,2,10,"ABC670105139"
TEXT 310,160,"4",0,1,1,"RM0"
PRINT 1
EOP
"""


try:
    # Send the clear buffer command to the printer first
    printer.write(0x02, clear_buffer.encode('ascii'))
    
    # Then send the actual ZPL data for the label
    printer.write(0x02, zpl_data.encode('ascii'))
    
    print("ZPL print command sent successfully!")
except usb.core.USBError as e:
    print(f"Error: {e}")
finally:
    # Release the USB device
    usb.util.dispose_resources(printer)

