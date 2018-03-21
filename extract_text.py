#!/usr/bin/env python
import scrabulizer
import templates

import cv2
import numpy as np
import os
import sys
from math import sqrt

MATCH_THRESHOLD = 0.7
COLUMNS=8
ROWS=7
RACK_LETTERS=7

TEMPLATES = templates.build_templates()
RACK_TEMPLATES = templates.build_rack_templates()
ICON_TEMPLATES = templates.build_icon_templates()

def dist_2d(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    xd, yd = x1 - x2, y1 - y2

    return sqrt(xd * xd + yd * yd)

def closest_cell(x, y, img_width, img_height):
    max_y = int(img_height * 0.85)
    x_coords = [int(bx) for bx in np.linspace(0, img_width, COLUMNS + 1)][:-1]
    y_coords = [int(by) for by in np.linspace(0, max_y, ROWS + 1)][:-1]
    points = [(bx, by) for by in y_coords for bx in x_coords]
    point_coords = [(point, (i % COLUMNS, i // COLUMNS)) for (i, point) in enumerate(points)]

    distances = [(dist_2d((x, y), pt), coord) for (pt, coord) in point_coords]

    return sorted(distances, key=lambda t: t[0])[0][1]

def closest_rack(x, y, img_width, img_height):
    ry = int(img_height * 0.85)
    rack_points = [(int(rx), ry) for rx in np.linspace(0, img_width, RACK_LETTERS + 1)][:-1]
    distances = [(dist_2d((x, y), pt), coord) for (coord, pt) in enumerate(rack_points)]

    return sorted(distances, key=lambda t: t[0])[0][1]

def parse_board(image, debug=False):
    max_y, max_x = image.shape

    rack_cutoff = 0.85 * max_y
    bonus_keys = ["2L", "2W", "3L", "3W"]

    print("Parsing board...")

    board = {}

    for letter, letter_templates in TEMPLATES.items():
        for template in letter_templates:
            res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(res >= MATCH_THRESHOLD)
            potential_matches = list(zip(*locations[::-1]))

            for (x, y) in potential_matches:
                if y > rack_cutoff:
                    continue

                percent_match = res[y][x]
                cx, cy = closest_cell(x, y, max_x, max_y)

                if (cx, cy) in board:
                    (cur_letter, cur_match) = board[(cx, cy)]
                    if percent_match > cur_match:
                        if debug and (cx, cy) == (7, 0):
                            print("Found better match at {}, {} with {} ({}%)".format(cx, cy, letter, percent_match))
                        board.update({(cx, cy): (letter, percent_match)})
                    else:
                        if debug and (cx, cy) == (7, 0):
                            print("Existing match at {}, {} with {} ({}%) better than {} ({}%)".format(cx, cy, cur_letter, cur_match, letter, percent_match))
                        continue
                else:
                    if debug and (cx, cy) == (7, 0):
                        print("Nothing yet for {}, {}, adding {} ({}%)".format(cx, cy, letter, percent_match))
                    board.update({(cx, cy): (letter, percent_match)})

    board = {k:v for k,v in  sorted(board.items(), key=lambda t: (t[0][1], t[0][0]))}

    bonuses = {k: l for k, (l, p) in board.items() if l in bonus_keys}
    board = {k: l for k, (l, p) in board.items() if l not in bonus_keys}

    return board, bonuses

def parse_rack(image, debug=False):
    max_y, max_x = image.shape

    rack_cutoff = 0.85 * max_y

    print("Parsing rack...")

    rack = {}

    for letter, letter_templates in RACK_TEMPLATES.items():
        for template in letter_templates:
            res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(res >= MATCH_THRESHOLD)
            potential_matches = list(zip(*locations[::-1]))

            for (x, y) in potential_matches:
                if y <= rack_cutoff:
                    continue

                percent_match = res[y][x]
                cx = closest_rack(x, y, max_x, max_y)

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

    return [letter for _, (letter, _) in sorted(rack.items(), key=lambda t: t[0])]

def get_board_bounds(image, debug=False):
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    top_offset, bottom_offset = 40, 0

    for text, icon_templates in ICON_TEMPLATES.items():
        for template in icon_templates:
            h, w = template.shape
            res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(res >= MATCH_THRESHOLD)
            potential_matches = list(zip(*locations[::-1]))

            for (x, y) in potential_matches:
                if debug:
                    print("Found potential {} at {}, {} ({}%)".format(text, x, y, res[y][x]*100))
                min_x = min(min_x, x)
                max_x = max(max_x, x + w)
                min_y = min(min_y, y + h + top_offset)
                max_y = max(max_y, y - bottom_offset)

    if float('-inf') in [max_x, max_y]:
        board_bounds_error("Unable to find shuffle icon.")

    if float('inf') in [min_x, min_y]:
        board_bounds_error("Unable to find back button or '0 snaps' label.")

    expected_aspect_ratio = 1.0558139534883721
    new_width = int(round((max_y - min_y) / expected_aspect_ratio))
    min_x = max(0, max_x - new_width)

    return (min_x, min_y, max_x, max_y)

def board_bounds_error(message):
    print(message)
    print("If you're using an emulator, it might be missing or outside of the size ranges this currently checks.")
    print("Try the Windows 8/10 version at: https://www.microsoft.com/store/games/snap-attack/9wzdncrfhwf6")
    print("If you are using the Windows version, try resizing the window, then re-docking it to the side of the screen.")
    sys.exit(1)

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

def load_image(file_name):
    if not os.path.exists(file_name):
        print("{} does not exist.".format(file_name))
        sys.exit(1)

    if not os.path.isfile(file_name):
        print("{} exists, but is not a file.".format(file_name))
        sys.exit(1)

    image = cv2.imread(file_name)

    if image is not None and image.any():
        return image

    print("Unable to load image: {}".format(file_name))
    sys.exit(1)

def cleanup_original(input_file, debug=False):
    # Trim original to just include known back/shuffle buttons
    color = load_image(input_file)
    gray, x, y = to_grayscale(color)

    bounding_box = get_board_bounds(gray, debug)

    if True:
        print("Bounding box: {}".format(bounding_box))
    sub_image, x, y = get_sub_image(color, bounding_box)

    return cv2.resize(sub_image, (645, 681))

def load_grayscale(input_file):
    image = load_image(input_file)
    return to_grayscale(image)

def print_board(board, bonuses, rack):
    joined_board = board.copy()
    joined_board.update(bonuses)

    print("  | A| B| C| D| E| F| G| H|")
    for y in range(7):
        print("{} |".format(y + 1), end='')
        for x in range(8):
            print("{}|".format(joined_board.get((x, y), "").rjust(2, " ")), end='')
        print('')

    print("Rack: {}".format("".join(rack)))

def process(input_file, options={}):
    dry_run = options.get('dry_run', True)
    debug = options.get('debug', False)
    cleanup = options.get('cleanup', False)

    filename_base = templates.filename_without_ext(input_file)

    os.makedirs('cleaned_input', exist_ok=True)

    bounded = cleanup_original(input_file, debug)

    # Write it to cleaned_input dir
    cleaned_filename = 'cleaned_input/{}.png'.format(filename_base)
    cv2.imwrite(cleaned_filename, bounded)

    # Load that as our actual input
    image, x, y = load_grayscale(cleaned_filename)

    print("{}: {}x{}".format(cleaned_filename, x, y))

    board, bonuses = parse_board(image, debug)
    rack = parse_rack(image, debug)

    print_board(board, bonuses, rack)

    moves = scrabulizer.scrape_scrabulizer(board, rack, bonuses, dry_run)

    print("-----------------")

    for move in moves:
        print(move)

    if cleanup:
        try:
            os.remove(cleaned_filename)
        except OSError:
            pass

    return board, bonuses, rack, moves

if __name__ == "__main__":
    process(sys.argv[1], {'debug': False})

