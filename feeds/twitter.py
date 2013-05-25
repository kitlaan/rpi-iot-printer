#!/usr/bin/env python

# This is a modification of the Python port of Adafruit's "Gutenbird"
# sketch for Arduino.  Polls one or more Twitter accounts for changes,
# displaying updates on attached thermal printer.
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
import urllib, json, HTMLParser
from unidecode import unidecode

def feed(printer, args, state):
    """ Main entry point for Twitter Feed """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return

    # query can be any valid Twitter API search string, including
    # boolean operators.  See https://dev.twitter.com/docs/using-search
    # for options and syntax.  Funny characters do NOT need to be URL
    # encoded here -- urllib takes care of that.
    if 'query' not in args or not args['query']:
        return

    # We shouldn't need to change this, but it's an option...
    if 'server' not in args or not args['server']:
        args['server'] = 'search.twitter.com'
    if 'max' not in args or not args['max']:
        args['max'] = '3'
    if 'spacing' not in args or not args['spacing']:
        args['spacing'] = '3'

    # we stash the last message ID so we resume from a location
    if 'lastId' not in state:
        state['lastId'] = '1'

    # parse out params
    try:
        feed_lines = int(args['spacing'])
        if feed_lines < 1:
            feed_lines = 1
        if feed_lines > 5:
            feed_lines = 5
    except:
        feed_lines = 3

    # try to fetch the tweets...
    url = ( 'http://' + args['server'] + '/search.json?' +
            urllib.urlencode(dict(q=args['query'])) +
            '&rpp=' + args['max'] +
            '&since_id=' + state['lastId'] )
    try:
        data = json.load(urllib.urlopen(url))
        state['lastId'] = data['max_id_str']
    except:
        return

    # process the tweets
    if 'results' not in data or not data['results']:
        return

    for tweet in data['results']:
        if 'from_user' not in tweet \
                or 'created_at' not in tweet \
                or 'text' not in tweet:
            continue

        printer.inverseOn()
        printer.print(' ' + '{:<31}'.format(tweet['from_user']))
        printer.inverseOff()

        printer.underlineOn()
        printer.print('{:<32}'.format(tweet['created_at']))
        printer.underlineOff()

        # Remove HTML escape sequences
        # and remap Unicode values to nearest ASCII equivalents
        printer.print(unidecode(
            HTMLParser.HTMLParser().unescape(tweet['text'])))

        printer.feed(feed_lines)


if __name__ == '__main__':
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    state = {'lastId':'1'}
    feed(printer, {'query':'from:Adafruit', 'count':'2'}, state)
    print("lastId = %s" % (state['lastId']))
