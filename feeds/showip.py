#!/usr/bin/env python

# Print the system IP address.
#
# Originally written by Adafruit Industries.  MIT license.
# Modified by Ted M Lin.
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
import os, socket

def feed(printer, args, state):
    """ Main entry point for IP Fetch Feed """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return

    # Grab the IP address by connecting to Google
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 0))
        ip_addr = s.getsockname()[0]

        printer.print('My IP address is ' + ip_addr)
        printer.feed(3)

    except:
        printer.boldOn()
        printer.println('Network is unreachable.')
        printer.boldOff()
        printer.print('Connect display and keyboard\n'
                      'for network troubleshooting.')
        printer.feed(3)

        import signal, inspect
        handler = signal.getsignal(signal.SIGINT)
        if not inspect.isbuiltin(handler):
            os.kill(os.getpid(), signal.SIGINT)
        else:
            return


if __name__ == '__main__':
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {}, {})
