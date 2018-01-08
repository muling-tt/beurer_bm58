# beurer_bm58
Import data from Beurer BM 58.

Apparently there are at least two versions of the BM 58 out there:

* Connected via USB-Serial converter (New ttyUSB device created) -> [This is for you](https://github.com/DaveDavenport/BPM)
* Connected as HID device: "0c45:7406 Microdia" -> This script might work for you (verified up to serial numbers starting with 2017C31)

Both users are read and printed or added to an sqlite db file. More info https://muling.lu/beurer-bm58

To read data as user edit "10_beurer.rules" and change the OWNER to your user. Copy the file to your udev directory (e.g. /etc/udev/rules.d/) and replug the device.

## Upgrade
If you upgrade from an earlier version without user support, you need to update your database:   
```alter table measures add user text;```
