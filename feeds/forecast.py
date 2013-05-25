#!/usr/bin/python

# Weather forecast for Raspberry Pi w/Adafruit Mini Thermal Printer.
# Retrieves data from Yahoo! weather, prints current conditions and
# forecasts for next two days.  See timetemp.py for a different
# weather example using nice bitmaps.
#
# Originally written by Adafruit Industries.  MIT license.
# Modified by Ted M Lin.
# 
# Required software includes Adafruit_Thermal and PySerial libraries.
# Other libraries used are part of stock Python install.
# 
# Resources:
# http://www.adafruit.com/products/597 Mini Thermal Receipt Printer
# http://www.adafruit.com/products/600 Printer starter pack

from __future__ import print_function
import urllib
from xml.dom.minidom import parseString
from unidecode import unidecode

deg = chr(0xf8) # Degree symbol on thermal printer

def gettag(dom, tag, idx):
    return dom.getElementsByTagName(tag)[idx]

def get_forecast(woeid):
    try:
        # Fetch forecast data from Yahoo!, parse resulting XML
        dom = parseString(urllib.urlopen(
            'http://weather.yahooapis.com/forecastrss?w=' + woeid).read())

        data = {}

        data['heading'] = gettag(dom,'description',0).firstChild.data

        data['cur-data'] = gettag(dom,'pubDate', 0).firstChild.data
        data['cur-temp'] = gettag(dom,'yweather:condition',0).getAttribute('temp')
        data['cur-cond'] = gettag(dom,'yweather:condition',0).getAttribute('text')

        data['today-day']  = gettag(dom,'yweather:forecast',0).getAttribute('day')
        data['today-lo']   = gettag(dom,'yweather:forecast',0).getAttribute('low')
        data['today-hi']   = gettag(dom,'yweather:forecast',0).getAttribute('high')
        data['today-cond'] = gettag(dom,'yweather:forecast',0).getAttribute('text')

        data['tomm-day']  = gettag(dom,'yweather:forecast',1).getAttribute('day')
        data['tomm-lo']   = gettag(dom,'yweather:forecast',1).getAttribute('low')
        data['tomm-hi']   = gettag(dom,'yweather:forecast',1).getAttribute('high')
        data['tomm-cond'] = gettag(dom,'yweather:forecast',1).getAttribute('text')

        for key in data:
            data[key] = unidecode(data[key])

        return data
    except:
        return None

def feed(printer, args, state):
    """ Main entry point for Time and Temperature Feed """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return

    # WOEID indicates the geographic location for the forecast.  It is
    # not a ZIP code or other common indicator.  Instead, it can be found
    # by 'manually' visiting http://weather.yahoo.com, entering a location
    # and requesting a forecast, then copy the number from the end of the
    # current URL string and paste it here.
    if 'location' not in args or not args['location']:
        return

    data = get_forecast(args['location'])
    if not data:
        return

    printer.inverseOn()
    printer.print('{:^32}'.format(data['heading']))
    printer.inverseOff()
    printer.print('{:^32}'.format(data['cur-data']))
    cond = data['cur-temp'] + deg + ' ' + data['cur-cond']
    printer.print('{:^32}'.format(cond))

    printer.feed(2)

    cond = "%s: lo %4s  hi %4s" % (data['today-day'],
                                   data['today-lo'] + deg, data['today-hi'] + deg)
    printer.print('{:^32}'.format(cond))
    printer.print('{:^32}'.format(data['today-cond']))

    cond = "%s: lo %4s  hi %4s" % (data['tomm-day'],
                                   data['tomm-lo'] + deg, data['tomm-hi'] + deg)
    printer.print('{:^32}'.format(cond))
    printer.print('{:^32}'.format(data['tomm-cond']))

    printer.feed(3)


if __name__ == '__main__':
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {'location':'2373572'}, {})
