#!/usr/bin/env python

# Current time and temperature display for Raspberry Pi w/Adafruit Mini
# Thermal Printer.  Retrieves data from Yahoo! weather, prints current
# conditions and time using large, friendly graphics.
# See forecast.py for a different weather example that's all text-based.
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
from xml.dom.minidom import parseString
import Image, ImageDraw, time, urllib, os

# Although the Python Imaging Library does have nice font support,
# I opted here to use a raster bitmap for all of the glyphs instead.
# This allowed lots of control over kerning and such, and I didn't
# want to spend a lot of time hunting down a suitable font with a
# permissive license.
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
symbol_file = os.path.join(root_dir, 'gfx', 'timetemp.png')
symbols = Image.open(symbol_file)   # Bitmap w/all chars & symbols

# These are the widths of certain glyphs within the 'symbols' bitmap
TimeDigitWidth = [  38,  29,  38,  36,  40,  35,  37,  37, 38, 37, 13 ]
TempDigitWidth = [  33,  25,  32,  31,  35,  30,  32,  32, 33, 32, 17, 14 ]
DateDigitWidth = [  16,  13,  16,  15,  17,  15,  16,  16, 16, 16 ]
HumiDigitWidth = [  14,  10,  14,  13,  15,  12,  13,  13, 13, 13, 18 ]
DayWidth       = [ 104, 109,  62, 110,  88, 110,  95 ]
MonthWidth     = [  53,  52,  60,  67,  59,  63,  59,  56, 51, 48, 54, 53 ]
DirWidth       = [  23,  35,  12,  27,  15,  33,  19,  41, 23 ]
DirAngle       = [  23,  68, 113, 157, 203, 247, 293, 336 ]

# Generate a list of sub-image glyphs cropped from the symbols image
def croplist(widths, x, y, height):
    cropped = []
    for i in range(len(widths)):
	cropped.append(symbols.crop(
            [x, y+i*height, x+widths[i], y+(i+1)*height]))
    return cropped

# Crop glyph lists (digits, days of week, etc.)
TimeDigit = croplist(TimeDigitWidth,   0,   0, 44)
TempDigit = croplist(TempDigitWidth,  40,   0, 39)
DateDigit = croplist(DateDigitWidth,  75,   0, 18)
HumiDigit = croplist(HumiDigitWidth,  75, 180, 16)
Day       = croplist(DayWidth      ,  93,   0, 25)
Month     = croplist(MonthWidth    ,  93, 175, 24)
Dir       = croplist(DirWidth      , 162, 175, 21)

# Crop a few odds-and-ends glyphs (not in lists)
Wind      = symbols.crop([  93, 463, 157, 479 ])
Humidity  = symbols.crop([  93, 479, 201, 500 ])
Kph       = symbols.crop([ 156, 366, 196, 386 ])
Mph       = symbols.crop([ 156, 387, 203, 407 ])

# Paste a series of glyphs (mostly numbers) from string to img
def drawNums(img, string, x, y, glyph_list):
    for i in range(len(string)):
        d = ord(string[i]) - ord('0')
        img.paste(glyph_list[d], (x, y))
        x += glyph_list[d].size[0] + 1
    return x

# Determine total width of a series of glyphs in string
def numWidth(string, glyph_list):
    w_sum = 0
    for i in range(len(string)):
        d = ord(string[i]) - ord('0')
        if i > 0:
            w_sum += 1 # extra space between digits
        w_sum += glyph_list[d].size[0]
    return w_sum

def get_weather(woeid):
    try:
        # Fetch weather data from Yahoo!, parse resulting XML
        dom = parseString(urllib.urlopen(
            'http://weather.yahooapis.com/forecastrss?w=' + woeid).read())

        # Extract values relating to current temperature, humidity, wind
        temperature = int(dom.getElementsByTagName(
                        'yweather:condition')[0].getAttribute('temp'))
        humidity    = int(dom.getElementsByTagName(
                        'yweather:atmosphere')[0].getAttribute('humidity'))
        windSpeed   = int(dom.getElementsByTagName(
                        'yweather:wind')[0].getAttribute('speed'))
        windDir     = int(dom.getElementsByTagName(
                        'yweather:wind')[0].getAttribute('direction'))
        windUnits   = dom.getElementsByTagName(
                        'yweather:units')[0].getAttribute('speed')

        return (temperature, humidity, windSpeed, windDir, windUnits)
    except:
        return

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

    weather = get_weather(args['location'])
    if not weather:
        return
    (temperature, humidity, windSpeed, windDir, windUnits) = weather

    # Generate the working image
    img  = Image.new("1", [330, 117], "white")
    draw = ImageDraw.Draw(img)

    # Draw top & bottom bars
    draw.rectangle([42,   0, 330,   3], fill="black")
    draw.rectangle([42, 113, 330, 116], fill="black")

    # Initial drawing position
    x = 42
    y = 12

    # Render current time (always 24 hour XX:XX format)
    t = time.localtime()
    drawNums(img, time.strftime("%H:%M", t), x, y, TimeDigit)

    # Determine wider of day-of-week or date (for alignment)
    s = str(t.tm_mday) # Convert day of month to a string
    w = MonthWidth[t.tm_mon - 1] + 6 + numWidth(s, DateDigit)
    if DayWidth[t.tm_wday] > w: w = DayWidth[t.tm_wday]

    # Draw day-of-week and date
    x = img.size[0] - w                    # Left alignment for two lines
    img.paste(Day[t.tm_wday], (x, y))      # Draw day of week word
    y += 27                                # Next line
    img.paste(Month[t.tm_mon - 1], (x, y)) # Draw month word
    x += MonthWidth[t.tm_mon - 1] + 6      # Advance past month
    drawNums(img, s, x, y, DateDigit)      # Draw day of month

    # Position for temperature
    x = 42 
    y = 67

    # Degrees to string, remap '-' glyph, append degrees glyph
    s = str(temperature).replace('-', ';') + ':'
    drawNums(img, s, x, y, TempDigit)

    # Determine wider of humidity or wind info
    s  = str(humidity) + ':' # Appends percent glyph
    s2 = str(windSpeed)
    winDirNum = 0  # Wind direction glyph number
    if windSpeed > 0:
        for winDirNum in range(len(DirAngle) - 1):
            if windDir < DirAngle[winDirNum]:
                break
    w  = Humidity.size[0] + 5 + numWidth(s, HumiDigit)
    w2 = Wind.size[0] + 5 + numWidth(s2, HumiDigit)
    if windSpeed > 0:
        w2 += 3 + Dir[winDirNum].size[0]
    if windUnits == 'kph':
        w2 += 3 + Kph.size[0]
    else:
        w2 += 3 + Mph.size[0]
    if w2 > w:
        w = w2

    # Draw humidity and wind
    x = img.size[0] - w # Left-align the two lines
    y = 67
    img.paste(Humidity, (x, y))
    x += Humidity.size[0] + 5
    drawNums(img, s, x, y, HumiDigit)
    x = img.size[0] - w # Left-align again
    y += 23             # And advance to next line
    img.paste(Wind, (x, y))
    x += Wind.size[0] + 5
    if windSpeed > 0:
        img.paste(Dir[winDirNum], (x, y))
        x += Dir[winDirNum].size[0] + 3
    x = drawNums(img, s2, x, y, HumiDigit) + 3
    if windUnits == 'kph':
        img.paste(Kph, (x, y))
    else:
        img.paste(Mph, (x, y))

    # Output the image
    #img.save('timetemp_sample.jpg', "JPEG")
    printer.printImage(img, True)
    printer.feed(3)

if __name__ == '__main__':
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {'location':'2459115'}, {})
