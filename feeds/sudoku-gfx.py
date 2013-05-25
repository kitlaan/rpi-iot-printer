#!/usr/bin/python
#
# Sudoku Generator, using 'sudoku' program
#
# Written by Ted M Lin.  MIT license.

from __future__ import print_function
import os, subprocess, Image

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sudoku_file = os.path.join(root_dir, 'gfx', 'sudoku.png')
bg = Image.open(sudoku_file)

xcoord  = [ 15, 55,  95,  139, 179, 219,  263, 303, 343 ]
ycoord  = [ 56, 96, 136,  180, 220, 260,  304, 344, 384 ]

# Crop number bitmaps out of source image
numbers = []
for i in range(9):
  numbers.append(bg.crop([384, i*28, 410, (i+1)*28]))


def feed(printer, args, state):
    """ Main entry point for Sudoku Feed """
    if not printer:
        return
    if not isinstance(args, dict) or not isinstance(state, dict):
        return

    if not bg or not numbers:
        return

    try:
        game = subprocess.check_output(["/usr/games/sudoku", "-g1", "-fcompact"])
        lines = filter(None, game.split('\n'))
        lines = [line.strip() for line in lines]

        difficulty = "unknown"
        if lines[0].startswith('%'):
            difficulty = lines[0].split(' - ', 2)[1]
            lines = lines[1:]

        data = ''.join(lines)
    except:
        return
    if not data or len(data) != 81:
        return

    img = Image.new("1", [384, 426], "white")

    img.paste(bg, (0, 0))
    try:
        for col in xrange(9):
            for row in xrange(9):
                idx = row * 9 + col
                c = data[idx]
                if c != '.':
                    img.paste(numbers[int(c)-1], (xcoord[col], ycoord[row]))
    except:
        return

    #img.save("demo.jpg")
    printer.printImage(img, True)
    printer.println("RATING: ", difficulty) 
    printer.feed(3)

if __name__ == '__main__':
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(parent_dir)

    from Adafruit_Thermal import Adafruit_Thermal
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)

    feed(printer, {}, {})
