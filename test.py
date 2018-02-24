#!/usr/bin/env python
import scrabulizer
import templates

import cv2
import numpy as np
import os
import sys
from math import sqrt

MATCH_THRESHOLD = 0.9
RECT_SIZE = 80
TEMPLATES = templates.build_templates()
RACK_TEMPLATES = templates.build_rack_templates()
ICON_TEMPLATES = templates.build_icon_templates()

def dist_2d(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    xd, yd = x1 - x2, y1 - y2

    return sqrt(xd * xd + yd * yd)

def get_board_points():
    x_coords = [0, 81, 161, 242, 322, 403, 483, 564]
    y_coords = [3, 83, 163, 243, 324, 405, 484]

    points = [(x, y) for y in y_coords for x in x_coords]
    return [(coord, (i % 8, i // 8)) for (i, coord) in enumerate(points)]

def get_rack_points():
    y = 598
    padding = 12
    x_coords = range(5, 648, RECT_SIZE + padding)

    points = [(x, y) for x in x_coords]
    return [(coord, i) for (i, coord) in enumerate(points)]

GRID_COORDINATES = get_board_points()
RACK_COORDINATES = get_rack_points()

def closest_cell(x, y):
    distances = [(dist_2d((x, y), pt), coord) for (pt, coord) in GRID_COORDINATES]

    return sorted(distances, key=lambda t: t[0])[0][1]

def closest_rack(x, y):
    distances = [(dist_2d((x, y), pt), coord) for (pt, coord) in RACK_COORDINATES]

    return sorted(distances, key=lambda t: t[0])[0][1]

def to_grayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_TOZERO | cv2.THRESH_OTSU)[1]

    (y, x) = gray.shape

    return (gray, x, y)

def load_grayscale(input_file):
    image = cv2.imread(input_file)
    return to_grayscale(image)

def parse_board(image, debug=False):
    max_y, max_x = image.shape

    rack_cutoff = 0.85 * max_y
    bonus_keys = ["2L", "2W", "3L", "3W"]

    if debug:
        print("Parsing board...")

    board = {}

    for letter, template in TEMPLATES.items():
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= MATCH_THRESHOLD)
        potential_matches = list(zip(*locations[::-1]))

        for (x, y) in potential_matches:
            if y > rack_cutoff:
                continue

            percent_match = res[y][x]
            cx, cy = closest_cell(x, y)

            if (cx, cy) in board:
                (cur_letter, cur_match) = board[(cx, cy)]
                if percent_match > cur_match:
                    if debug:
                        print("Found better match at {}, {} with {} ({}%)".format(cx, cy, letter, percent_match))
                    board.update({(cx, cy): (letter, percent_match)})
                else:
                    if debug:
                        print("Existing match at {}, {} with {} ({}%) better than {} ({}%)".format(cx, cy, cur_letter, cur_match, letter, percent_match))
                    continue
            else:
                if debug:
                    print("Nothing yet for {}, {}, adding {} ({}%)".format(cx, cy, letter, percent_match))
                board.update({(cx, cy): (letter, percent_match)})

    if debug:
        print(board)

    bonuses = {k: l for k, (l, p) in board.items() if l in bonus_keys}
    board = {k: l for k, (l, p) in board.items() if l not in bonus_keys}

    return board, bonuses

def parse_rack(image, debug=False):
    max_y, max_x = image.shape

    rack_cutoff = 0.85 * max_y

    if debug:
        print("Parsing rack...")

    rack = {}

    for letter, template in RACK_TEMPLATES.items():
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= MATCH_THRESHOLD)
        potential_matches = list(zip(*locations[::-1]))

        for (x, y) in potential_matches:
            if y <= rack_cutoff:
                continue

            percent_match = res[y][x]
            cx = closest_rack(x, y)

            if cx in rack:
                (cur_letter, cur_match) = rack[cx]
                if percent_match > cur_match:
                    if debug:
                        print("Found better match at {} with {} ({}%)".format(cx, letter, percent_match))
                    rack.update({cx: (letter, percent_match)})
                else:
                    if debug:
                        print("Existing match at {} with {} ({}%) better than {} ({}%)".format(cx, cur_letter, cur_match, letter, percent_match))
                    continue
            else:
                if debug:
                    print("Nothing yet for {}, adding {} ({}%)".format(cx, letter, percent_match))
                rack.update({cx: (letter, percent_match)})

    rack = [letter for _, (letter, _) in sorted(rack.items(), key=lambda t: t[0])]

    if debug:
        print(rack)

    return rack

def process(input_file, options):
    dry_run = options.get('dry_run', True)
    debug = options.get('debug', False)

    image, x, y = load_grayscale(input_file) 

    print("{}: {}x{}".format(input_file, x, y))
    board, bonuses = parse_board(image, debug)
    print("board: {}".format(board))
    print("bonuses: {}".format(bonuses))
    rack = parse_rack(image, debug)

if __name__ == "__main__":
    process(sys.argv[1], {'debug': True})

