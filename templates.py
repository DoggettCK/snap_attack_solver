#!/usr/bin/env python
import cv2
import numpy as np
import os
import os.path
import glob

DEFAULT_RESOLUTION = (1920, 1080)
TEMPLATE_SCALES = {
        (1920, 1080): {
            "board": [1, 1],
            "rack": [1, 1],
            "shuffle": [1, 1],
            "back": [1, 1]
            },
        (1600, 900): {
            "board": [0.8375, 0.8375],
            "rack": [0.8375, 0.8375],
            "shuffle": [0.8103448276, 0.82],
            "back": [0.86, 0.86]
            },

        (1440, 900): {
            "board": [0.725, 0.725],
            "rack": [0.725, 0.7125],
            "shuffle": [0.8103448276, 0.84],
            "back": [0.84, 0.84]
            },

        }

def filename_without_ext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def get_filenames(pattern):
    return [(filename_without_ext(f), f) for f in glob.glob(pattern)]

def load_images(filename, resolution, image_type):
    image = cv2.imread(filename, 0)
    clean_file = filename_without_ext(filename)
    y, x = image.shape

    scales = TEMPLATE_SCALES.get(resolution, TEMPLATE_SCALES.get(DEFAULT_RESOLUTION))
    x_scale, y_scale = scales.get(image_type, [1, 1])

    if resolution != DEFAULT_RESOLUTION:
        return cv2.resize(image, None, fx=x_scale, fy=y_scale)
    else:
        return image

def build_templates(resolution):
    bonuses_pattern = 'templates/bonuses/*.png'
    letters_pattern = 'templates/letters/[A-Z].png'

    bonuses = {l: load_images(fn, resolution, 'board') for (l, fn) in get_filenames(bonuses_pattern)}
    letters = {l: load_images(fn, resolution, 'board') for (l, fn) in get_filenames(letters_pattern)}

    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates(resolution):
    rack_pattern = 'templates/rack/[A-Z].png'

    return {l: load_images(fn, resolution, 'rack') for (l, fn) in get_filenames(rack_pattern)}

def build_icon_templates(resolution):
    icon_pattern = 'templates/*.png'

    return {l: load_images(fn, resolution, l) for (l, fn) in get_filenames(icon_pattern)}
