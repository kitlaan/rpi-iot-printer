#!/usr/bin/env python

# Write a short 'fortune'
#
# Written by Ted M Lin.  MIT license.
# 
# Required hardware includes an Internet-connected system with Python
# (such as Raspberry Pi) and an Adafruit Mini Thermal Receipt printer
# and all related power supplies and cabling.
# Required software includes Adafruit_Thermal and PySerial libraries.
# 
# Resources:
# http://www.adafruit.com/products/597 Mini Thermal Receipt Printer
# http://www.adafruit.com/products/600 Printer starter pack

from __future__ import print_function
import subprocess, textwrap

def feed(printer, args, state):
    """ Main entry point for Fortune Feed """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return

    try:
        fortune = subprocess.check_output(["/usr/games/fortune", "-s"])
        lines = filter(None, fortune.split('\n'))
        lines = [line.strip() for line in lines]
        text = ' '.join(lines)
        output = textwrap.wrap(text, 32)
    except:
        return
    if not output:
        return

    printer.boldOn()
    printer.println('Fortune:')
    printer.boldOff()

    for line in output:
        printer.println(line)
    printer.feed(3)


if __name__ == '__main__':
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {}, {})
