#!/usr/bin/env python
import scrabulizer
from PIL import Image
import pytesseract
import requests
import cv2
import numpy as np
import os
import os.path
import glob
import re
import sys
import json

MATCH_THRESHOLD = 0.6

def filename_without_ext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def letter_images(pattern):
    return [(filename_without_ext(f), f) for f in glob.glob(pattern)]

def build_templates():
    bonuses_pattern = 'templates/bonuses/*.png'
    letters_pattern = 'templates/letters/[A-Z].png'

    bonuses = {l: cv2.imread(fn, 0) for (l, fn) in letter_images(bonuses_pattern)}
    letters = {l: cv2.imread(fn, 0) for (l, fn) in letter_images(letters_pattern)}

    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates():
    rack_pattern = 'templates/rack/[A-Z].png'

    return {l: cv2.imread(fn, 0) for (l, fn) in letter_images(rack_pattern)}

def build_icon_templates():
    icon_pattern = 'templates/*.png'

    return {l: cv2.imread(fn, 0) for (l, fn) in letter_images(icon_pattern)}

TEMPLATES = build_templates()
RACK_TEMPLATES = build_rack_templates()
ICON_TEMPLATES = build_icon_templates()

def get_board_rects(image):
    y_coords = [136, 217, 297, 377, 458, 538, 618]
    x_coords = [8, 89, 169, 250, 330, 410, 491, 571]
    rect_size = 80

    return [image[y:y+rect_size, x:x+rect_size] for y in y_coords for x in x_coords]

def get_rack_rects(image):
    y = 733
    rect_size = 80
    padding = 12
    x_coords = range(13, 648, rect_size + padding)

    return [image[y:y+rect_size, x:x+rect_size] for x in x_coords]

def get_board_bounds(image):
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

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

    return (min_x, min_y, max_x, max_y)

def get_sub_image(image, bounds):
    (min_x, min_y, max_x, max_y) = bounds

    return image[min_y:max_y, min_x:max_x]

def extract_color_images(input_file, output_dir):
    image = cv2.imread(input_file)

    for index, img in enumerate(get_board_rects(image)):
        x, y = index % 8, index // 8
        filename = "{}/color_board_{}_{}.png".format(output_dir, x, y)
        cv2.imwrite(filename, img)

    for index, img in enumerate(get_rack_rects(image)):
        filename = "{}/color_rack_{}.png".format(output_dir, index)
        cv2.imwrite(filename, img)

    pass

def to_grayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.threshold(gray, 0, 255, cv2.THRESH_TOZERO | cv2.THRESH_OTSU)[1]

def cleanup_original(input_file):
    color = cv2.imread(input_file)
    (y, x, _) = color.shape
    print("{} (original): {}x{} aspect ratio: {}".format(input_file, x, y, y/x))
    gray = to_grayscale(color)

    bounding_box = get_board_bounds(gray)

    sub_image = get_sub_image(color, bounding_box)
    (y, x, _) = sub_image.shape
    print("{} (bounded): {}x{} aspect ratio: {}".format(input_file, x, y, y/x))
    return cv2.resize(sub_image, (645, 837))

def load_grayscale(input_file):
    image = cv2.imread(input_file)

    return to_grayscale(image)

def text_from_image(image):
    return pytesseract.image_to_string(Image.fromarray(image), lang='eng', boxes=False, config="-psm 7")

def format_move(move_tuple):
    (word, x, y, direction) = move_tuple

    if direction == '0':
        direction = 'horizontal'
    else:
        direction = 'vertical'

    return "{} ({}, {}) ({})".format(word, x, y, direction)

def guess_letter(image, templates, debug=False):
    matches = []
    for (text, template) in templates.items():
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(res >= MATCH_THRESHOLD)
        if(len(list(zip(*locations[::-1])))) > 0:
            matches.append((text, res[0][0]))

    # TODO: Refactor this now that you understand it better from get_board_bounds
    matches = sorted(matches, key=lambda match: -match[1])

    if any(matches):
        if debug:
            print(matches)
        return (True, matches[0][0])
    else:
        return (False, None)

def process(input_file, options):
    scrape = options.get('scrape', True)
    debug = options.get('debug', False)

    pid = os.getpid()
    output_dir = "output/{}_{}".format(pid, filename_without_ext(input_file))
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('cleaned_input', exist_ok=True)
    
    # TODO: Remove once you have all templates
    # extract_color_images(input_file, output_dir)

    # Trim original to just include known back/shuffle buttons
    bounded = cleanup_original(input_file)

    # Write it to cleaned_input dir
    filebase = filename_without_ext(input_file)
    cleaned_filename = 'cleaned_input/{}.png'.format(filebase)
    cv2.imwrite(cleaned_filename, bounded)

    # Load that as our actual input
    image = load_grayscale(cleaned_filename) 
    (y, x) = image.shape
    print("{}: {}x{} aspect ratio: {}".format(cleaned_filename, x, y, y/x))

    board = {}
    bonuses = {}
    rack = []

    if True:
        sys.exit(0)

    # TODO: Get rid of tesseract after you've gotten examples of every letter and just use opencv matching
    print("Parsing board...")
    for index, img in enumerate(get_board_rects(image)):
        x, y = index % 8, index // 8

        matched, letter = guess_letter(img, TEMPLATES)
        if matched:
            if letter in ["3W", "3L", "2W", "2L"]:
                bonuses.update({(x, y): letter})
            else:
                board.update({(x, y): letter})
        else:
            pass

    if debug:
        print("Board: {}".format(board))
        print("Bonuses: {}".format(bonuses))

    print("Parsing rack...")
    for index, img in enumerate(get_rack_rects(image)):
        matched, letter = guess_letter(img, RACK_TEMPLATES)
        if matched:
            rack.append(letter)
        else:
            letter = text_from_image(img[20:, 20:])
            print("rack letter: {}".format(letter))
            filename = "output/{}/rack_{}.png".format(pid, letter.lower())
            cv2.imwrite(filename, img) # TODO: Remove after debugging
            rack.append(letter)

    if debug:
        print("Rack: {}".format("".join(rack)))

    if scrape:
        print("Querying Scrabulizer...")
        moves = scrabulizer.scrape_scrabulizer(board, rack, bonuses)
        for move in moves:
            # TODO: Recursively call until rack is empty
            print(move)
    print("-----------------")

if __name__ == "__main__":
    process(sys.argv[1], {'debug': True, 'scrape': False})

