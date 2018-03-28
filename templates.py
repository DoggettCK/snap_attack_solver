#!/usr/bin/env python
import cv2
import numpy as np
import os
import os.path
import glob

# Expected tile sizes from 1920x1080
BOARD_TILE_X = 80
BOARD_TILE_Y = 80
RACK_TILE_X = 80
RACK_TILE_Y = 80
SHUFFLE_TILE_X = 58
SHUFFLE_TILE_Y = 50
BACK_TILE_X = 50
BACK_TILE_Y = 50

DEFAULT_RESOLUTION = (1920, 1080)
TEMPLATE_SCALES = {
        (1920, 1080): {
            "board": [1, 1],
            "rack": [1, 1],
            "shuffle": [1, 1],
            "back": [1, 1]
            },
        (1680, 1050): {
            "board": [72 / BOARD_TILE_X, 72 / BOARD_TILE_Y],
            "rack": [73 / RACK_TILE_X, 73 / RACK_TILE_Y],
            "shuffle": [50 / SHUFFLE_TILE_X, 45 / SHUFFLE_TILE_Y],
            "back": [43 / BACK_TILE_X, 43 / BACK_TILE_Y]
            },
        (1680, 1050, 'nexus4'): {
            "board": [72 / BOARD_TILE_X, 73 / BOARD_TILE_Y],
            "rack": [75 / RACK_TILE_X, 75 / RACK_TILE_Y],
            },
        (1600, 900): {
            "board": [67 / BOARD_TILE_X, 67 / BOARD_TILE_Y],
            "rack": [67 / RACK_TILE_X, 67 / RACK_TILE_Y],
            "shuffle": [47 / SHUFFLE_TILE_X, 41 / SHUFFLE_TILE_Y],
            "back": [43 / BACK_TILE_X, 43 / BACK_TILE_Y]
            },
        (1440, 900): {
            "board": [58 / BOARD_TILE_X, 58 / BOARD_TILE_Y],
            "rack": [58 / RACK_TILE_X, 57 / RACK_TILE_Y],
            "shuffle": [47 / SHUFFLE_TILE_X, 42 / SHUFFLE_TILE_Y],
            "back": [42 / BACK_TILE_X, 42 / BACK_TILE_Y]
            },
        (1280, 1024): {
            "board": [69 / BOARD_TILE_X, 69 / BOARD_TILE_Y],
            "rack": [70 / RACK_TILE_X, 70 / RACK_TILE_Y],
            "shuffle": [48 / SHUFFLE_TILE_X, 42 / SHUFFLE_TILE_Y],
            "back": [41 / BACK_TILE_X, 41 / BACK_TILE_Y]
            },
        (1280, 960): {
            "board": [62 / BOARD_TILE_X, 62 / BOARD_TILE_Y],
            "rack": [63 / RACK_TILE_X, 63 / RACK_TILE_Y],
            "shuffle": [49 / SHUFFLE_TILE_X, 42 / SHUFFLE_TILE_Y],
            "back": [42 / BACK_TILE_X, 42 / BACK_TILE_Y]
            },
        }

def supported_resolutions():
    resolutions = []

    for scale in TEMPLATE_SCALES.keys():
        fmt = "{}x{}"
        if len(scale) == 3:
            fmt = "{}x{} ({})"
        resolutions.append(fmt.format(*scale))

    return "Currently supported resolutions: {}".format(resolutions)

def resolution_supported(resolution):
    return resolution in TEMPLATE_SCALES.keys()

def filename_without_ext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def get_filenames(pattern):
    return [(filename_without_ext(f), f) for f in glob.glob(pattern)]

def load_image(filename):
    return cv2.imread(filename, 0)

def load_and_scale_image(filename, resolution, image_type):
    image = cv2.imread(filename, 0)

    if resolution == DEFAULT_RESOLUTION:
        return image

    clean_file = filename_without_ext(filename)

    scales = TEMPLATE_SCALES.get(resolution, TEMPLATE_SCALES.get(DEFAULT_RESOLUTION))
    x_scale, y_scale = scales.get(image_type, [1, 1])

    return cv2.resize(image, None, fx=x_scale, fy=y_scale)

def build_board_templates(resolution):
    bonuses_pattern = 'templates/bonuses/*.png'
    letters_pattern = 'templates/letters/[A-Z].png'

    bonuses = {l: load_and_scale_image(fn, resolution, 'board') for (l, fn) in get_filenames(bonuses_pattern)}
    letters = {l: load_and_scale_image(fn, resolution, 'board') for (l, fn) in get_filenames(letters_pattern)}

    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates(resolution):
    rack_pattern = 'templates/rack/[A-Z].png'

    return {l: load_and_scale_image(fn, resolution, 'rack') for (l, fn) in get_filenames(rack_pattern)}

def build_icon_templates(resolution):
    icon_pattern = 'templates/*.png'

    return {l: load_and_scale_image(fn, resolution, l) for (l, fn) in get_filenames(icon_pattern)}

def build_system_templates():
    system_pattern = 'templates/system/*.png'

    return {l: load_image(fn) for (l, fn) in get_filenames(system_pattern)}
