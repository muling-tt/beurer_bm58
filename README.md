# beurer_bm58
Import data from Beurer BM 58.

Apparently there are at least two versions of the BM 58 out there:

* Connected via USB-Serial converter (New ttyUSB device created) -> [This is for you](https://github.com/DaveDavenport/BPM)
* Connected as HID device: "0c45:7406 Microdia" -> This script might work for you

This is a very ugly POC script to read out data from the BM 58, it doesn't know anything about U2 (user 2).

More info on reversing Beurer (specifically the BM65 via USB/Serial) can be found at [atbrasks blog](http://www.atbrask.dk/?p=98)
