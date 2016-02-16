#!/usr/bin/env python

import usb.core
import usb.util
import usb.control
import string

vendor_id = 0x0c45
product_id = 0x7406

# Find the USB device
dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
if dev is None:
    raise ValueError("device not found")

# Set the one and only config
dev.set_configuration()

# Initialize and get identifier
init_bytes = [0xaa, 0xa4, 0xa5, 0xa6, 0xa7]
term_bytes = [0xf7, 0xf6]
get_record_count_byte = [0xa2]
get_record_byte = [0xa3]
padding = [0xf4, 0xf4, 0xf4, 0xf4, 0xf4, 0xf4, 0xf4]
rx_buf = []

for i in init_bytes:
    dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, [i] + padding)
    rx_buf += dev.read(0x81,8)

rx_data = ''.join([chr(x) for x in rx_buf])
print "Identifier: '" + filter(lambda x: x in string.printable, rx_data)[1:] + "'"
 
# Get available record count
dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, get_record_count_byte +  padding)
record_count = dev.read(0x81,8)[0]
print "Records in memory: " + str(record_count)

# Read records
for i in range(record_count):
    dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, get_record_byte + [i + 1] + padding)
    record = dev.read(0x81,8)
    i += 1
    sys = record[0] + 25
    dia = record[1] + 25
    pul = record[2]
    mth = record[3]
    day = record[4]
    h   = record[5]
    m   = record[6]

    print "Date: " + str(day) + "." + str(mth) + ", Time: " + str(h) +  ":" + str(m)  + ", SYS: " + str(sys) + ", DIA: " + str(dia) + ", PUL: " + str(pul)

# Terminate
for i in term_bytes:
    dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, [i] + padding)

