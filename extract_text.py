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

def get_board_rects(image):
    y_coords = [3, 83, 163, 243, 324, 405, 484]
    x_coords = [0, 81, 161, 242, 322, 403, 483, 564]

    return [image[y:y+RECT_SIZE, x:x+RECT_SIZE] for y in y_coords for x in x_coords]

def get_rack_rects(image):
    y = 598
    padding = 12
    x_coords = range(5, 648, RECT_SIZE + padding)

    return [image[y:y+RECT_SIZE, x:x+RECT_SIZE] for x in x_coords]

def get_board_bounds(image):
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    # TODO: back button can be way off to the side, need to figure out better way to just get board bounds
    for (text, template) in ICON_TEMPLATES.items():
        h, w = template.shape
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= 0.90)
        potential_matches = list(zip(*locations[::-1]))

        for (x, y) in potential_matches:
            min_x = min(min_x, x)
            max_x = max(max_x, x + w)
            min_y = min(min_y, y)
            max_y = max(max_y, y + h)

    (y_lower_offset, _) = ICON_TEMPLATES['back'].shape
    min_y = min_y + y_lower_offset + 46 # 46px should go from bottom of back button to top of grid

    (y_upper_offset, _) = ICON_TEMPLATES['shuffle'].shape
    max_y = max_y - y_upper_offset - 10

    expected_aspect_ratio = 1.0558139534883721
    new_width = int(round((max_y - min_y) / expected_aspect_ratio))
    min_x = max_x - new_width

    return (min_x, min_y, max_x, max_y)

def get_sub_image(image, bounds):
    (min_x, min_y, max_x, max_y) = bounds

    sub_image = image[min_y:max_y, min_x:max_x]

    (y, x, _) = sub_image.shape

    return (sub_image, x, y)

def to_grayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_TOZERO | cv2.THRESH_OTSU)[1]

    (y, x) = gray.shape

    return (gray, x, y)

def cleanup_original(input_file):
    # Trim original to just include known back/shuffle buttons
    color = cv2.imread(input_file)
    gray, x, y = to_grayscale(color)

    bounding_box = get_board_bounds(gray)

    sub_image, x, y = get_sub_image(color, bounding_box)

    return cv2.resize(sub_image, (645, 681))

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

    for index, img in enumerate(get_board_rects(image)):
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

def setup(filename_base):
    for directory in ['input', 'cleaned_input', 'output', 'templates']:
        os.makedirs(directory, exist_ok=True)

    pid = os.getpid()
    output_dir = "output/{}_{}".format(pid, filename_base)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('cleaned_input', exist_ok=True)

def process(input_file, options):
    dry_run = options.get('dry_run', True)
    debug = options.get('debug', False)

    filename_base = templates.filename_without_ext(input_file)

    setup(filename_base)

    bounded = cleanup_original(input_file)

    # Write it to cleaned_input dir
    cleaned_filename = 'cleaned_input/{}.png'.format(filename_base)
    cv2.imwrite(cleaned_filename, bounded)

    # Load that as our actual input
    image, x, y = load_grayscale(cleaned_filename) 

    print("{}: {}x{}".format(cleaned_filename, x, y))

    board, bonuses = parse_board(image, debug)
    rack = parse_rack(image, debug)

    moves = scrabulizer.scrape_scrabulizer(board, rack, bonuses, dry_run)

    print("-----------------")

    for move in moves:
        print(move)

    if not debug:
        try:
            os.remove(cleaned_filename)
        except OSError:
            pass

if __name__ == "__main__":
    process(sys.argv[1], {'debug': True})

