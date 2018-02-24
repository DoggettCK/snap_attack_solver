#!/usr/bin/env python
import scrabulizer
import templates

import cv2
import numpy as np
import os
import sys

MATCH_THRESHOLD = 0.6
RECT_SIZE = 80
TEMPLATES = templates.build_templates()
RACK_TEMPLATES = templates.build_rack_templates()
ICON_TEMPLATES = templates.build_icon_templates()

def get_board_points():
    y_coords = [3, 83, 163, 243, 324, 405, 484]
    x_coords = [0, 81, 161, 242, 322, 403, 483, 564]

    points = [(y, x) for y in y_coords for x in x_coords]
    return [(coord, (i % 8, i // 8)) for (i, coord) in enumerate(points)]

def to_grayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_TOZERO | cv2.THRESH_OTSU)[1]

    (y, x) = gray.shape

    return (gray, x, y)

def load_grayscale(input_file):
    image = cv2.imread(input_file)
    return to_grayscale(image)

def guess_letter(image, templates, debug=False):
    match = None
    match_percent = float('-inf')

    # TODO: Refactor this to take the entire board. Since it's been cleaned and
    # trimmed down to size, I can make an educated guess about the board
    # coordinates based on what approximate eighth of the width/height it falls
    # in, without having to be super-precise about pixel values. That should
    # let more oddly-shaped boards be playable.

    for (letter, template) in templates.items():
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= MATCH_THRESHOLD)
        potential_matches = list(zip(*locations[::-1]))

        for (x, y) in potential_matches:
            if res[y][x] > match_percent:
                match_percent = res[y][x]
                match = letter

    if debug and match:
        print("Highest match: {} ({}%)".format(match, match_percent * 100))
        return match

def parse_board(image, debug=False):
    if debug:
        print("Parsing board...")

    board = {}
    bonuses = {}

    for index, img in enumerate(get_board_points(image)):
        x, y = index % 8, index // 8

        matched = guess_letter(img, TEMPLATES, debug)
        if matched:
            if matched in ["3W", "3L", "2W", "2L"]:
                bonuses.update({(x, y): matched})
            else:
                board.update({(x, y): matched})
        else:
            pass

    if debug:
        print("Board: {}".format(board))
        print("Bonuses: {}".format(bonuses))

    return board, bonuses

def parse_rack(image, debug=False):
    if debug:
        print("Parsing rack...")

    rack = []

    for index, img in enumerate(get_rack_rects(image)):
        matched = guess_letter(img, RACK_TEMPLATES, debug)
        if matched:
            rack.append(matched)
        else:
            if debug:
                print("Unable to detect rack letter at index {}".format(index))
            pass

    if debug:
        print("Rack: {}".format("".join(rack)))

    return rack


def process(input_file, options):
    dry_run = options.get('dry_run', True)
    debug = options.get('debug', False)

    image, x, y = load_grayscale(input_file) 

    print("{}: {}x{}".format(input_file, x, y))
    print(get_board_points())
    sys.exit()

    board, bonuses = parse_board(image, debug)
    rack = parse_rack(image, debug)

    moves = scrabulizer.scrape_scrabulizer(board, rack, bonuses, dry_run)

    print("-----------------")

    for move in moves:
        print(move)

    if not debug:
        try:
            os.remove(input_file)
        except OSError:
            pass

if __name__ == "__main__":
    process(sys.argv[1], {'debug': True})

