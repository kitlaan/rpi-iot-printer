#!/usr/bin/env python

# Welcome image for Raspberry Pi w/Adafruit Mini Thermal Printer.
#
# Originally written by Adafruit Industries.  MIT license.
# Modified by Ted M Lin.
#
# Required software includes Adafruit_Thermal, Python Imaging and PySerial
# libraries. Other libraries used are part of stock Python install.
#
# Resources:
# http://www.adafruit.com/products/597 Mini Thermal Receipt Printer
# http://www.adafruit.com/products/600 Printer starter pack

from __future__ import print_function
import Image

def feed(printer, args, state):
    """ Main entry point for Drawing Image """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return

    if not 'file' in args or not args['file']:
        return

    try:
        img = Image.open(args['file'])
    except:
        return

    # Output the image
    printer.printImage(img, True)
    printer.feed(3)

if __name__ == '__main__':
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {'file':'../gfx/hello.png'}, {})
