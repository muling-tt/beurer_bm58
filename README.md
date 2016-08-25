# beurer_bm58
Import data from Beurer BM 58.

Apparently there are at least two versions of the BM 58 out there:

* Connected via USB-Serial converter (New ttyUSB device created) -> [This is for you](https://github.com/DaveDavenport/BPM)
* Connected as HID device: "0c45:7406 Microdia" -> This script might work for you

Currently only reads out data from user 1 (U1). More info https://muling.lu/beurer-bm58

Copy "10_beurer.rules" file to your udev directory to read data as user.
