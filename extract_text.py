#!/usr/bin/env python
import scrabulizer
import templates

import cv2
import numpy as np
import os
import sys
from math import sqrt

COLUMNS=8
ROWS=7
RACK_LETTERS=7
MATCH_THRESHOLD = 0.7
BOARD_RACK_SPLIT_RATIO = 0.85

def dist_2d(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    xd, yd = x1 - x2, y1 - y2

    return sqrt(xd * xd + yd * yd)

def closest_cell(x, y, img_width, img_height):
    max_y = int(img_height * BOARD_RACK_SPLIT_RATIO)
    x_coords = [int(bx) for bx in np.linspace(0, img_width, COLUMNS + 1)][:-1]
    y_coords = [int(by) for by in np.linspace(0, max_y, ROWS + 1)][:-1]
    points = [(bx, by) for by in y_coords for bx in x_coords]
    point_coords = [(point, (i % COLUMNS, i // COLUMNS)) for (i, point) in enumerate(points)]

    distances = [(dist_2d((x, y), pt), coord) for (pt, coord) in point_coords]

    return sorted(distances, key=lambda t: t[0])[0][1]

def closest_rack(x, y, img_width, img_height):
    ry = int(img_height * BOARD_RACK_SPLIT_RATIO)
    rack_points = [(int(rx), ry) for rx in np.linspace(0, img_width, RACK_LETTERS + 1)][:-1]
    distances = [(dist_2d((x, y), pt), coord) for (coord, pt) in enumerate(rack_points)]

    return sorted(distances, key=lambda t: t[0])[0][1]

def parse_board(image, board_templates, options):
    debug = options.get('debug', False)
    max_y, max_x = image.shape

    rack_cutoff = BOARD_RACK_SPLIT_RATIO * max_y
    bonus_keys = ["2L", "2W", "3L", "3W"]

    print("Parsing board...")

    board = {}

    for letter, template in board_templates.items():
        for (x, y, percent_match) in get_template_matches(image, template):
            if y > rack_cutoff:
                continue

            cx, cy = closest_cell(x, y, max_x, max_y)

            if (cx, cy) in board:
                (cur_letter, cur_match) = board[(cx, cy)]
                if percent_match > cur_match:
                    if debug:
                        print("Found better match at {}, {} with {} ({}%)".format(cx, cy, letter, percent_match * 100))
                    board.update({(cx, cy): (letter, percent_match)})
                else:
                    if debug:
                        print("Existing match at {}, {} with {} ({}%) better than {} ({}%)".format(cx, cy, cur_letter, cur_match * 100, letter, percent_match * 100))
                    continue
            else:
                if debug:
                    print("Nothing yet for {}, {}, adding {} ({}%)".format(cx, cy, letter, percent_match * 100))
                board.update({(cx, cy): (letter, percent_match)})

    board = {k:v for k,v in  sorted(board.items(), key=lambda t: (t[0][1], t[0][0]))}

    bonuses = {k: l for k, (l, p) in board.items() if l in bonus_keys}
    board = {k: l for k, (l, p) in board.items() if l not in bonus_keys}

    return board, bonuses

def parse_rack(image, rack_templates, options):
    debug = options.get('debug', False)
    system = options.get('system')

    threshold = MATCH_THRESHOLD

    if system in ['nexus4', 'galaxy_note_edge']:
        threshold = 0.5

    max_y, max_x = image.shape

    rack_cutoff = BOARD_RACK_SPLIT_RATIO * max_y

    print("Parsing rack...")

    rack = {}

    for letter, template in rack_templates.items():
        for (x, y, percent_match) in get_template_matches(image, template, threshold):
            if y <= rack_cutoff:
                continue

            cx = closest_rack(x, y, max_x, max_y)

            if cx in rack:
                (cur_letter, cur_match) = rack[cx]
                if percent_match > cur_match:
                    if debug:
                        print("Found better match at {} with {} ({}%)".format(cx, letter, percent_match * 100))
                    rack.update({cx: (letter, percent_match)})
                else:
                    if debug:
                        print("Existing match at {} with {} ({}%) better than {} ({}%)".format(cx, cur_letter, cur_match * 100, letter, percent_match * 100))
                    continue
            else:
                if debug:
                    print("Nothing yet for {}, adding {} ({}%)".format(cx, letter, percent_match * 100))
                rack.update({cx: (letter, percent_match)})

    return [letter for _, (letter, _) in sorted(rack.items(), key=lambda t: t[0])]

def get_template_matches(image, template, threshold=MATCH_THRESHOLD):
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(res >= threshold)

    potential_matches = list(zip(*locations[::-1]))

    return [(x, y, res[y][x]) for x, y in potential_matches]

def get_system(original_image, system_templates):
    gray, _, _ = to_grayscale(original_image)
    for system, template in system_templates.items():
        if(any(get_template_matches(gray, template))):
            return system

    return "windows"

def get_board_bounds(image, icon_templates, options):
    debug = options.get('debug', False)
    system = options.get('system', 'windows')

    if system == 'nexus4':
        return [3, 169, 563, 745]
    if system == 'galaxy_note_edge':
        return [8, 152, 542, 734]

    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    top_offset, bottom_offset = 40, 0

    for text, template in icon_templates.items():
        h, w = template.shape

        for (x, y, percent) in get_template_matches(image, template):
            if debug:
                print("Found potential {} at {}, {} ({}%)".format(text, x, y, percent*100))
            min_x = min(min_x, x)
            max_x = max(max_x, x + w)
            min_y = min(min_y, y + h + top_offset)
            max_y = max(max_y, y - bottom_offset)

    if float('-inf') in [max_x, max_y]:
        board_bounds_error("Unable to find shuffle icon.")

    if float('inf') in [min_x, min_y]:
        board_bounds_error("Unable to find back button or '0 snaps' label.")

    return (min_x, min_y, max_x, max_y)

def board_bounds_error(message):
    lines = [
            message,
            templates.supported_resolutions(),
            "Try docking Snap Attack to the right or left, by clicking/dragging the title bar to either side of the screen, or hitting the Windows key + the left or right arrow.",
            "Make sure when checking your resolution that the text/layout scaling is set to 100%.",
            "If you're using an emulator, it might be missing or outside of the size ranges this currently checks.",
            "Try the Windows 8/10 version at: https://www.microsoft.com/store/games/snap-attack/9wzdncrfhwf6",
            "If you are using the Windows version, try resizing the window, then re-docking it to the side of the screen.",
            ]
    print("\n\n".join(lines))
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

def cleanup_original(input_file, original_image, icon_templates, options):
    debug = options.get('debug', False)

    # Trim original to just include known back/shuffle buttons
    gray, x, y = to_grayscale(original_image)

    bounding_box = get_board_bounds(gray, icon_templates, options)

    if debug:
        print("Bounding box: {}".format(bounding_box))
    sub_image, x, y = get_sub_image(original_image, bounding_box)

    return sub_image

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

    system_templates = templates.build_system_templates()

    original_image = load_image(input_file)
    system = get_system(original_image, system_templates)
    options['system'] = system

    if system != 'windows':
        resolution = options.get('resolution', (1920, 1080)) + (system, )
        options['resolution'] = resolution

    resolution = options.get('resolution', (1920, 1080))
    if not templates.resolution_supported(resolution):
        board_bounds_error("Unsupported resolution: {}x{}".format(*resolution))

    board_templates = templates.build_board_templates(resolution)
    rack_templates = templates.build_rack_templates(resolution)
    icon_templates = templates.build_icon_templates(resolution)

    filename_base = templates.filename_without_ext(input_file)

    os.makedirs('cleaned_input', exist_ok=True)

    bounded = cleanup_original(input_file, original_image, icon_templates, options)

    # Write it to cleaned_input dir
    cleaned_filename = 'cleaned_input/{}.png'.format(filename_base)
    cv2.imwrite(cleaned_filename, bounded)

    # Load that as our actual input
    image, x, y = load_grayscale(cleaned_filename)

    print("{}: {}x{}".format(cleaned_filename, x, y))

    board, bonuses = parse_board(image, board_templates, options)
    rack = parse_rack(image, rack_templates, options)

    print_board(board, bonuses, rack)

    moves = scrabulizer.scrape_scrabulizer(board, rack, bonuses, dry_run)

    print("-----------------")

    for move in moves:
        print(move)

    return board, bonuses, rack, moves

if __name__ == "__main__":
    process(sys.argv[1], {'debug': False})
    # process('tests/fixtures/13852_1600x900.png', {'debug': False, 'resolution': (1600, 900)})
    # process('tests/fixtures/J0iV6v1_1600x900.png', {'debug': False, 'resolution': (1600, 900)})
    # process('tests/fixtures/14144_1680x1050.png', {'debug': False, 'resolution': (1680, 1050)})
    # process('tests/fixtures/dL7B8Yj_nexus4_1680x1050.png', {'debug': False, 'resolution': (1680, 1050)})
    # process('tests/fixtures/11896_1920x1080.png', {'debug': False, 'resolution': (1920, 1080)})
    # process('tests/fixtures/11812_1920x1080.png', {'debug': False, 'resolution': (1920, 1080)})
    # process('tests/fixtures/2088_1920x1080.png', {'debug': False, 'resolution': (1920, 1080)})
    # process('tests/fixtures/9112_1920x1080.png', {'debug': False, 'resolution': (1920, 1080)})
    # TODO: 1280x1024 will be a special case because it has a weirdly-shaped board
    # process('tests/fixtures/14148_1280x1024.png', {'debug': False, 'resolution': (1280, 1024)})
    # TODO: 1280x960 will be a special case because it has a weirdly-shaped board
    # process('tests/fixtures/10236_1280x960.png', {'debug': False, 'resolution': (1280, 960)})
