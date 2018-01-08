#!/usr/bin/env python3

import usb.core
import datetime
import string
import sqlite3
import argparse
import logging

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x7406

LOGGER = logging.getLogger('BeurerBM58')

class BeurerConnectionException(Exception):
    """Beurer Connection Exception"""
    pass

class BeurerBM58(object):
    """This class interacts with the bm58 device and reads measurements from the device"""
    def __init__(self, vid, pid):
        self.vid = vid
        self.pid = pid
        self.padding = [0xf4, 0xf4, 0xf4, 0xf4, 0xf4, 0xf4, 0xf4]
        self.dev = None
        self._connect()

    def _send_to_device(self, data):
        """internal helper to send data to device"""
        LOGGER.debug('sending {0}'.format(data))
        #  bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength=None, timeout=None
        self.dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, data + self.padding)

    def _read_from_device(self, size):
        """internal helper to read data from device"""
        LOGGER.debug('reading data with size {0}'.format(size))
        result = self.dev.read(0x81, size)
        LOGGER.debug('returned {0} from device'.format(result))
        return result

    def _connect(self):
        """find the device in the usb subsystem and try to condect to it"""
        LOGGER.debug('searching for device with VendorID {0} and ProductID {1}'.format(self.vid, self.pid))
        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if self.dev is None:
            raise BeurerConnectionException("device not found")
        LOGGER.debug('found device {0} - manufacturer: {1} - serial_number: {2}'.format(self.dev.product,
                                                                                        self.dev.manufacturer,
                                                                                        self.dev.serial_number))
        # Detach usbhid driver
        if self.dev.is_kernel_driver_active(0):
            LOGGER.debug('device is in use by kernel driver so trying to detach it')
            try:
                self.dev.detach_kernel_driver(0)
            except usb.core.USBError as ex:
                BeurerConnectionException("Unable to detach kernel driver: %s" % str(ex))

        LOGGER.debug('set configuration active')
        self.dev.set_configuration()

    # Find USB device, initialize it and get identifier
    def initialize(self):
        """ initialize device and return the device identifier

        :returns: identifier
        """
        LOGGER.debug('send device initialization bytes, device will respond with identifier')
        init_bytes = [0xaa, 0xa4, 0xa5, 0xa6, 0xa7]
        rx_buf = []
        for i in init_bytes:
            self._send_to_device([i])
            rx_buf += self._read_from_device(8)

        rx_data = ''.join([chr(x) for x in rx_buf])
        identifier = ''.join(s for s in rx_data if s in string.printable)

        LOGGER.debug('return identifier {0}'.format(identifier))

        return identifier

    def record_count(self):
        """return the number of records stored on the device

        :returns: Number of Records
        """
        getrecord_count_byte = [0xa2]
        self._send_to_device(getrecord_count_byte)
        return self._read_from_device(8)[0]

    def get_records(self, count):
        """read the records from the device

        :param count int: number of records to read
        """
        getrecord_b = [0xa3]
        records = {}
        for i in range(count):
            self._send_to_device(getrecord_b + [i + 1])

            # Put everything in a nested dict
            dataset = self._read_from_device(8)
            records[i] = {}
            records[i]['systole'] = dataset[0] + 25
            records[i]['diastole'] = dataset[1] + 25
            records[i]['pulse'] = dataset[2]
            records[i]['month'] = dataset[3]
            records[i]['hour'] = dataset[5]
            records[i]['minute'] = dataset[6]
            records[i]['year'] = dataset[7]+2000

            day = dataset[4]
            if day > 128:
                 day = day - 128;
                 records[i]['user'] = 2
            else:
                 records[i]['user'] = 1
            records[i]['day'] = day

            i += 1

        return records

    # Terminate connection
    def terminate(self):
        """disconnect from the device"""
        LOGGER.debug('terminating connection')
        term_bytes = [0xf7, 0xf6]
        for i in term_bytes:
            self._send_to_device([i])
        self.dev.reset()

def write_to_stdout(data, filename=''):
    """write data to stdout

    :param data dict: Dictionary containing the measures
    :param filename: just a helper so sqlite and stdout class can look the same
    """
    print('{0} | {1:^20} | {2} | {3} | {4}'.format('USER', 'DATE', 'SYSTOLE',
                                             'DIASTOLE', 'PULSE'))
    print('-'*56)
    for m_id, measurement in data.items():
        date = datetime.datetime(int(measurement['year']), int(measurement['month']), int(measurement['day']),
                                 int(measurement['hour']), int(measurement['minute']))
        measurement.update({'date': str(date)})
        print('{user:^4} | {date:^20} | {systole:^7} | {diastole:^8} | {pulse:^5}'.format(**measurement))

def write_to_sqlite(data, filename):
    """write data to sqlite database

    :param data dict: Dictionary containing the measures
    :param filename str: Filename where to write the data to
    """
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''CREATE TABLE IF NOT EXISTS measures
                         (date text PRIMARY KEY, systole text, diastole text, pulse text, user text)''')

    for m_id, measurement in data.items():
        date = datetime.datetime(int(measurement['year']), int(measurement['month']), int(measurement['day']),
                                 int(measurement['hour']), int(measurement['minute']))
        measurement.update({'date': str(date)})
        LOGGER.debug('writing {date} - sys: {systole} dia: {diastole} pul: {pulse} u: {user}'.format(**measurement))
        # Insert a row of data
        cursor.execute("INSERT OR IGNORE INTO measures VALUES ('{date}', {systole}, {diastole}, {pulse}, {user})".format(**measurement))

    # Save (commit) the changes
    conn.commit()
    LOGGER.info('wrote {0} entries to Database'.format(len(data.items())))

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

def initialize_argument_parser():
    """Setup argument parser

    :returns: args
    """

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--parameter', action='store', default="defaultvalue",
                           help='default parameter (default: %(default)s)')
    argparser.add_argument('-l', '--loglevel', action='store', default="ERROR",
                           help='Loglevel to use (default: %(default)s)')
    argparser.add_argument('-o', '--output', action='store', choices=['sqlite', 'stdout'], default='stdout',
                           help='Where to output the Data (default: %(default)s)')
    argparser.add_argument('-f', '--filename', action='store', default='beurer.db',
                           help='Filename to write output to (when using sqlite)')

    args = argparser.parse_args()
    return args


def main():
    """helper main function to satisfy pylint"""

    args = initialize_argument_parser()
    logging.basicConfig(level=getattr(logging, args.loglevel))

    beurer = BeurerBM58(VENDOR_ID, PRODUCT_ID)
    identifier = beurer.initialize()
    LOGGER.info("Identified Device: '" + str(identifier) + "'")

    count = beurer.record_count()
    LOGGER.info("Records for User U1: " + str(count))

    records = beurer.get_records(count)

    beurer.terminate()

    globals()['write_to_' + args.output](records, args.filename)

if __name__ == "__main__":
    main()

# vim:filetype=python:foldmethod=marker:autoindent:expandtab:tabstop=4
