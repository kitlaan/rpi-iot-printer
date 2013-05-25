#!/usr/bin/env python

# Main script for Adafruit (RPi) Internet of Things Printer 2.
# Monitors button for taps and holds, and performs periodic and scheduled actions.
#
# Written by Ted M Lin. MIT license.
# Based on code from Adafruit Industries. MIT license.
#
# MUST BE RUN AS ROOT (due to GPIO access)
#
# Required software includes Adafruit_Thermal, Python Imaging and PySerial
# libraries. Other libraries used are part of stock Python install.
# Requires GPIO 0.5.1
#
# Resources:
# http://www.adafruit.com/products/597 Mini Thermal Receipt Printer
# http://www.adafruit.com/products/600 Printer starter pack

from __future__ import print_function
import sys, os, signal, time, inspect
from ConfigParser import RawConfigParser
import RPi.GPIO as GPIO
from Adafruit_Thermal import Adafruit_Thermal

class PrintManager(object):
    LED_PIN    = 18
    BUTTON_PIN = 23

    HOLD_TIME = 2    # seconds for long press
    TAP_TIME  = 0.01 # seconds debounce for taps

    FEED_DIR    = "feeds"
    CONFIG_FILE = "run.cfg"

    RUN_SCHEDULED_AT_START = True

    def __init__(self):
        # Initialize printer interface
        self.printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

        # Use Broadcom pin numbers (not Raspberry Pi pin numbers) for GPIO
        GPIO.setmode(GPIO.BCM)

        # Enable LED and button (w/pull-up on latter)
        GPIO.setup(self.LED_PIN, GPIO.OUT)
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Setup button handling
        self.button_hold = None
        self.button_tap = None
        self.prev_button_state = (GPIO.input(self.BUTTON_PIN), time.time())
        GPIO.add_event_detect(self.BUTTON_PIN, GPIO.BOTH, callback=self.button_handler)

        # Feed module manager
        sys.path.append(self.FEED_DIR)
        self.feeds = {}

        # Feed runtime configuration
        self.run_start = []
        self.run_stop = []
        self.run_tap = []
        self.run_hold = []
        self.run_interval = []
        self.run_when = []

        # register some signal handlers
        self.terminate = False
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def cleanup(self):
        GPIO.cleanup()

    def led_on(self):
        GPIO.output(self.LED_PIN, GPIO.HIGH)

    def led_off(self):
        GPIO.output(self.LED_PIN, GPIO.LOW)

    def signal_handler(self, signum, frame):
        """ Handle ctrl-c and button events """
        if signum == signal.SIGINT:
            self.terminate = True
        elif signum == signal.SIGALRM:
            self.button_handler(self.BUTTON_PIN)

    def button_handler(self, channel):
        """ Handle the button tap/hold states """
        if channel != self.BUTTON_PIN:
            return

        state = GPIO.input(self.BUTTON_PIN)
        now = time.time()
        delta = now - self.prev_button_state[1]

        if self.prev_button_state[0] != state:
            self.prev_button_state = (state, now)

            if state == GPIO.HIGH:
                self.button_hold = None

                # debounce the button tap and trigger action
                if delta > self.TAP_TIME and self.button_tap is None:
                    self.button_tap = True
                    os.kill(os.getpid(), signal.SIGALRM)
            else:
                self.button_tap = None

                # schedule a hold check
                signal.alarm(int(self.HOLD_TIME))

        elif state == GPIO.LOW:
            if delta >= self.HOLD_TIME and self.button_hold is None:
                self.button_hold = True
                self.button_tap = False

    def feed_loader(self, feed_name):
        """ Import the module and get the handler function """
        if feed_name in self.feeds:
            return self.feeds[feed_name]
        for filename in os.listdir(self.FEED_DIR):
            name, ext = os.path.splitext(filename)
            if ext == ".py" and name == feed_name:
                # remember, this can fail if script overlays existing module
                try:
                    mod = __import__(feed_name)
                    if hasattr(mod, "feed"):
                        spec = inspect.getargspec(mod.feed)
                        if len(spec[0]) != 3:
                            continue
                        self.feeds[feed_name] = mod.feed
                        return mod.feed
                except:
                    pass
        return None

    def load_config(self):
        """ Read the config file for feeds to run """
        now = time.localtime()
        now_time = now.tm_hour * 60 + now.tm_min

        config = RawConfigParser()
        config.read(self.CONFIG_FILE)

        for s in config.sections():
            if not config.has_option(s, 'feed'):
                print("feed '%s' missing 'feed' identifier" % (s))
                continue

            feed = self.feed_loader(config.get(s, 'feed'))
            if not feed:
                print("feed '%s' could not load module '%s'" % (s, config.get(s, 'feed')))
                continue

            if not config.has_option(s, 'mode'):
                print("feed '%s' missing 'mode' identifier" % (s))
                continue
            mode = config.get(s, 'mode').lower()

            args = {}
            for o in filter(lambda x: x.startswith('@'), config.options(s)):
                args[o[1:]] = config.get(s, o)

            feed_item = {'id':s, 'feed':feed, 'args':args, 'state':{}}

            if mode == 'off':
                pass
            elif mode == 'start':
                self.run_start.append(feed_item)
            elif mode == 'stop':
                self.run_stop.append(feed_item)
            elif mode == 'hold':
                self.run_hold.append(feed_item)
            elif mode == 'tap':
                self.run_tap.append(feed_item)
            elif mode == 'interval':
                if not config.has_option(s, 'interval'):
                    print("feed '%s' missing 'interval' value" % (s))
                    continue
                try:
                    feed_item['interval'] = int(config.get(s, 'interval'))
                except:
                    print("feed '%s' has invalid 'interval' value" % (s))
                    continue

                feed_item['next'] = 0
                self.run_interval.append(feed_item)
            elif mode == 'at':
                if not config.has_option(s, 'when'):
                    print("feed '%s' missing 'at' value" % (s))
                    continue
                try:
                    t = time.strptime(config.get(s, 'when'), "%H:%M")
                    feed_item['when'] = t.tm_hour * 60 + t.tm_min
                except:
                    print("feed '%s' has invalid 'at' value" % (s))
                    continue

                if feed_item['when'] > now_time or self.RUN_SCHEDULED_AT_START:
                    feed_item['ran_today'] = False
                else:
                    feed_item['ran_today'] = True

                self.run_when.append(feed_item)
            else:
                print("feed '%s' has bad 'mode' value '%s'" % (s, mode))
                continue

    def run(self):
        """ Main loop that processing feeds """
        # starting program, run hello feeds
        self.do_jobs(self.run_start)

        while not self.terminate:
            now = time.localtime()
            now_time = now.tm_hour * 60 + now.tm_min

            # next run is at most 30sec away
            next_run = 30

            # button hold triggered
            if self.button_hold:
                self.button_hold = False
                self.do_jobs(self.run_hold)

            # button tap triggered
            if self.button_tap:
                self.button_tap = False
                self.do_jobs(self.run_tap)

            # look for scheduled feeds to run
            when_tasks = []
            for t in self.run_when:
                if t['when'] <= now_time:
                    if not t['ran_today']:
                        t['ran_today'] = True
                        when_tasks.append(t)
                else:
                    t['ran_today'] = False
            self.do_jobs(when_tasks)

            # look for interval feeds to run
            interval_tasks = []
            for t in self.run_interval:
                if t['next'] <= time.mktime(now):
                    t['next'] = time.mktime(now) + t['interval']
                    interval_tasks.append(t)
                if time.mktime(now) - t['next'] < next_run:
                    next_run = time.mktime(now) - t['next']

            self.do_jobs(interval_tasks)

            # wait until we have work to do
            if next_run >= 1:
                signal.alarm(next_run)
                signal.pause()
            else:
                time.sleep(0.25)

        # quitting program, run stop feeds
        self.do_jobs(self.run_stop)

    def do_jobs(self, feeds):
        if not feeds:
            return

        self.led_on()
        for f in feeds:
            try:
                f['feed'](self.printer, f['args'], f['state'])
            except:
                pass
        self.led_off()


if __name__ == '__main__':
    p = PrintManager()
    p.load_config()
    p.run()
    p.cleanup()
