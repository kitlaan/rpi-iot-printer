#!/usr/bin/python

# Google Calendar Reader.
#
# Written by Ted M Lin.  MIT License
# 
# Required software includes Adafruit_Thermal and PySerial libraries.
# Other libraries used are part of stock Python install.
# 
# Resources:
# http://www.adafruit.com/products/597 Mini Thermal Receipt Printer
# http://www.adafruit.com/products/600 Printer starter pack

from __future__ import print_function
import urllib, time, textwrap
from operator import itemgetter
from xml.dom.minidom import parseString
from unidecode import unidecode

def get_calendar(url, day, calname):
    try:
        url += '/full-noattendees' + \
               '?start-min=' + day + 'T00:00:00' + \
               '&start-max=' + day + 'T23:59:59' + \
               '&singleevents=true' + \
               '&orderby=starttime' + \
               '&max-results=100' + \
               '&fields=entry(title,gd:when)'

        dom = parseString(urllib.urlopen(url).read())

        entries = []
        for item in dom.getElementsByTagName('entry'):
            title = item.getElementsByTagName('title')[0].firstChild.data

            start = item.getElementsByTagName('gd:when')[0].getAttribute('startTime')
            start = start.split('.', 2)[0]
            if 'T' in start:
                starttime = time.strptime(start, "%Y-%m-%dT%H:%M:%S")
                starttime = "%02d:%02d" % (starttime.tm_hour, starttime.tm_min)
            else:
                starttime = ""

            entries.append((starttime, calname, unidecode(title)))

    except:
        entries = []

    return entries

def feed(printer, args, state):
    """ Main entry point for Time and Temperature Feed """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return
    if not args:
        return

    # the 'args' dictionary should consist of things like:
    # args['ME'] = 'user%40gmail.com/private-#######'
    # args['GP'] = 'ASDFG%40group.calendar.google.com/private-######'
    #
    # These come from the Google Calendar Atom Feed, by accessing
    # each calendar (via Calendar Settings/Details) and looking for
    # the 'Private Address' -- use the XML one.
    #
    # Then extract the URL snippet, leaving off the '/basic'

    feedprefix = 'https://www.google.com/calendar/feeds/'
    thedate = time.strftime("%Y-%m-%d")

    entries = []
    for feed in args:
        entries += get_calendar(feedprefix + args[feed], thedate, feed)
    entries = sorted(entries, key=itemgetter(0,2))

    # don't bother printing anything if there is nothing
    if not entries:
        return

    printer.inverseOn()
    printer.print('{:^32}'.format('CALENDAR for ' + thedate))
    printer.inverseOff()

    for item in entries:
        wrappedtitle = textwrap.wrap(item[2], 32, drop_whitespace=True,
                                     initial_indent='   ', subsequent_indent='   ')

        thetime = item[0]
        if not thetime:
            thetime = '-----'

        feeder = ''
        if item[1]:
            feeder = '(%s)' % (item[1])

        printer.println(thetime + ' ' + feeder)
        printer.println('\n'.join(wrappedtitle))

    printer.feed(3)

if __name__ == '__main__':
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {}, {})
