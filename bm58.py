import usb.core
import usb.util
import usb.control
import string

vendor_id = 0x0c45
product_id = 0x7406


class BeurerBM58():
    def __init__(self, vid, pid):
        self.vid = vid
        self.pid = pid
        self.padding = [0xf4, 0xf4, 0xf4, 0xf4, 0xf4, 0xf4, 0xf4]

    # Find USB device, initialize it and get identifier
    def initialize(self):
        init_bytes = [0xaa, 0xa4, 0xa5, 0xa6, 0xa7]
        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if self.dev is None:
            raise ValueError("device not found")

        # Detach usbhid driver
        if self.dev.is_kernel_driver_active(0):
            try:
                self.dev.detach_kernel_driver(0)
            except usb.core.USBError as e:
                sys.exit("Unable to detach kernel driver: %s" % str(e))

        # Set one and only configuration
        self.dev.set_configuration()

        # Send device initialization bytes, device will respond with identifier
        rx_buf = []
        for i in init_bytes:
            self.dev.ctrl_transfer(0x21, 0x09, 0x0200, 0, [i] + self.padding)
            rx_buf += self.dev.read(0x81, 8)
        rx_data = ''.join([chr(x) for x in rx_buf])
        identifier = filter(lambda x: x in string.printable, rx_data)[1:]
        return identifier

    # Get number of records
    def record_count(self):
        getrecord_count_byte = [0xa2]
        self.dev.ctrl_transfer(0x21,
                               0x09,
                               0x0200,
                               0,
                               getrecord_count_byte + self.padding)
        return self.dev.read(0x81, 8)[0]

    # Read records
    def get_records(self, count):
        getrecord_b = [0xa3]
        records = {}
        for i in range(count):
            self.dev.ctrl_transfer(0x21,
                                   0x09,
                                   0x0200,
                                   0,
                                   getrecord_b + [i + 1] + self.padding)

            # Put everything in a nested dict
            dataset = self.dev.read(0x81, 8)
            records[i] = {}
            records[i]['sys'] = dataset[0] + 25
            records[i]['dia'] = dataset[1] + 25
            records[i]['pul'] = dataset[2]
            records[i]['mth'] = dataset[3]
            records[i]['day'] = dataset[4]
            records[i]['h'] = dataset[5]
            records[i]['m'] = dataset[6]
            i += 1

        self.terminate()
        return records

    # Terminate connection
    def terminate(self):
        term_bytes = [0xf7, 0xf6]
        for i in term_bytes:
            self.dev.ctrl_transfer(0x21,
                                   0x09,
                                   0x0200,
                                   0,
                                   [i] + self.padding)


if __name__ == "__main__":
    beurer = BeurerBM58(vendor_id, product_id)
    identifier = beurer.initialize()
    count = beurer.record_count()
    records = beurer.get_records(count)

    print "Identifier: '" + identifier + "'"
    print "Records on device: " + str(count)

    for record in records.iteritems():
            print record
