#!/usr/bin/env python
import requests
import re

LETTER_SCORES = {
        'A': 2, 'B': 5, 'C': 3, 'D': 3, 'E': 1, 'F': 5,
        'G': 4, 'H': 4, 'I': 2, 'J': 10, 'K': 6, 'L': 3,
        'M': 4, 'N': 2, 'O': 2, 'P': 4, 'Q': 10, 'R': 2,
        'S': 2, 'T': 2, 'U': 4, 'V': 6, 'W': 6, 'X': 9,
        'Y': 5, 'Z': 10
        }

def format_move(move_tuple):
    (word, x, y, direction) = move_tuple

    if direction == '0':
        direction = 'horizontal'
    else:
        direction = 'vertical'

    return "{} ({}, {}) ({})".format(word, x, y, direction)

def scrape_scrabulizer(board, rack, bonuses, dry_run=False):
    if dry_run:
        return []

    print("Querying Scrabulizer...")

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
    blank_board = {"s_{0}_{1}".format(x, y): "" for x in range(0, 16) for y in range(0, 16)}
    blank_bonuses = {"b_{0}_{1}".format(x, y): "" for x in range(0, 16) for y in range(0, 16)}
    counts = {"tc{}".format(key): 1 for (key, value) in LETTER_SCORES.items()}
    scores = {"ts{}".format(key): value for (key, value) in LETTER_SCORES.items()}

    # Merge all default dicts into one
    base_board = { k: v for d in [options, blank_board, blank_bonuses, counts, scores] for k, v in d.items() }

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
            return []
    else:
        print("Unknown Scrabulizer response: {} {}".format(req.status_code, req.reason))
        return []

    return words
