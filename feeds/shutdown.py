#!/usr/bin/env python

# Just shutdown the machine
#
# Written by Ted M Lin.  MIT license.

from __future__ import print_function
import subprocess, time

def feed(printer, args, state):
    """ Main entry point for Shutdown """
    subprocess.call("sync")
    subprocess.call(["shutdown", "-h", "now"])
    time.sleep(120)

# Test handler so we don't require the main wrapper
if __name__ == '__main__':
    feed(None, {}, {})
