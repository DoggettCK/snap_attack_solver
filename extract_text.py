#!/usr/bin/env python
from PIL import Image
import pytesseract
import requests
import cv2
import numpy as np
import os
import re
import sys
import json

MATCH_THRESHOLD = 0.6

LETTER_SCORES = {
        'A': 1, 'B': 4, 'C': 4, 'D': 2, 'E': 1, 'F': 4,
        'G': 3, 'H': 3, 'I': 1, 'J': 10, 'K': 5, 'L': 2,
        'M': 4, 'N': 2, 'O': 1, 'P': 4, 'Q': 10, 'R': 1,
        'S': 1, 'T': 1, 'U': 2, 'V': 5, 'W': 4, 'X': 8,
        'Y': 3, 'Z': 10
        }

def build_templates():
    bonuses = {
            '2L': cv2.imread('templates/bonuses/2x_letter.png', 0),
            '2W': cv2.imread('templates/bonuses/2x_word.png', 0),
            '3L': cv2.imread('templates/bonuses/3x_letter.png', 0),
            '3W': cv2.imread('templates/bonuses/3x_word.png', 0),
            }
    letters = {c: cv2.imread('templates/letters/{}.png'.format(c.lower()), 0) for c in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}
    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates():
    # TODO: Finish out templates
    return {c: cv2.imread('templates/rack/rack_{}.png'.format(c.lower()), 0) for c in list('ADEFGHIKLNORSTUVY')}

TEMPLATES = build_templates()
RACK_TEMPLATES = build_rack_templates()

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

def cleanup_image(input_file):
    image = cv2.imread(input_file)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_TOZERO | cv2.THRESH_OTSU)[1]

    return image

def text_from_image(image):
    return pytesseract.image_to_string(Image.fromarray(image), lang='eng', boxes=False, config="-psm 7")

def blank_scrabulizer_board():
    options = {
            'dictionary': 4,
            'opponent_count': 1,
            'design': '',
            'sort_by': 0,
            'tc_': 0,
            'ts_': 0,
            'boardWidth': 8,
            'boardHeight': 7,
            'bingo1': 0,
            'bingo2': 0,
            'bingo3': 0,
            'bingo4': 0,
            'bingo5': 0,
            'bingo6': 0,
            'bingo7': 35,
            'bingo8': 50,
            'rackLength': 7
            }
    board = {"s_{0}_{1}".format(x, y): "" for x in range(0, 16) for y in range(0, 16)}
    bonuses = {"b_{0}_{1}".format(x, y): "" for x in range(0, 16) for y in range(0, 16)}
    counts = {"tc{}".format(key): 1 for (key, value) in LETTER_SCORES.items()}
    scores = {"ts{}".format(key): value for (key, value) in LETTER_SCORES.items()}

    # Merge all default dicts into one
    return { k: v for d in [options, board, bonuses, counts, scores] for k, v in d.items() }

def scrape_scrabulizer(board, rack, bonuses):
    url = 'https://www.scrabulizer.com/solver/results'
    headers = {
            'origin': 'http://www.scrabulizer.com',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'x-prototype-version': '1.7',
            'x-requested-with': 'XMLHttpRequest',
            'x-js-version': '3',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'referer': 'http://www.scrabulizer.com/',
            'authority': 'www.scrabulizer.com',
            'dnt': '1'
            }

    base_board = blank_scrabulizer_board()
    letters = {"s_{0}_{1}".format(x, y): letter for ((x, y), letter) in board.items()}
    bonuses = {"b_{0}_{1}".format(x, y): bonus for ((x, y), bonus) in bonuses.items()}
    rack = {'rack': ''.join(rack)} 

    payload = {k: v for d in [base_board, letters, bonuses, rack] for k, v in d.items()}

    req = requests.post(url, headers=headers, data=payload)

    words = []

    if req.status_code == 200:
        pattern = re.compile("moves = ([^;]+);")
        match = pattern.search(req.text)
        if match:
            words_string = match.groups()[0]
            words_pattern = re.compile("\[\"(\w+)\",\s*\[(\d+),\s*(\d+)\],\s*(\d+),")
            words = [format_move(move) for move in words_pattern.findall(words_string)]
        else:
            print("Unexpected Scrabulizer format. Couldn't find moves list.")
    else:
        print("Unknown Scrabulizer response: {} {}".format(req.status_code, req.reason))

    return words

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

    print("Input file: {}".format(input_file))
    image = cleanup_image(input_file)

    pid = os.getpid()
    os.mkdir("output/{}".format(pid))
    board = {}
    bonuses = {}
    rack = []

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

    os.rename('output/{}'.format(pid), 'output/{}'.format(''.join(rack)))

    cv2.waitKey(0)
    if debug:
        print("Rack: {}".format("".join(rack)))

    if scrape:
        print("Querying Scrabulizer...")
        moves = scrape_scrabulizer(board, rack, bonuses)
        for move in moves:
            # TODO: Recursively call until rack is empty
            print(move)
    print("-----------------")

if __name__ == "__main__":
    process(sys.argv[1], {'debug': True, 'scrape': False})

