#!/usr/bin/env python
import cv2
import numpy as np
import os
import os.path
import glob

MIN_SCALE = 0.5
MAX_SCALE = 1.5
SCALE_STEPS = 5

def filename_without_ext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def get_filenames(pattern):
    return [(filename_without_ext(f), f) for f in glob.glob(pattern)]

def load_images(filename, min_scale=MIN_SCALE, max_scale=MAX_SCALE, scale_steps=SCALE_STEPS):
    image = cv2.imread(filename, 0)

    images = [image]

    for scale in np.linspace(min_scale, max_scale, scale_steps):
        images.append(cv2.resize(image, None, fx=scale, fy=scale))

    return images

def build_templates(min_scale=MIN_SCALE, max_scale=MAX_SCALE, scale_steps=SCALE_STEPS):
    bonuses_pattern = 'templates/bonuses/*.png'
    letters_pattern = 'templates/letters/[A-Z].png'

    bonuses = {l: load_images(fn, min_scale, max_scale, scale_steps) for (l, fn) in get_filenames(bonuses_pattern)}
    letters = {l: load_images(fn, min_scale, max_scale, scale_steps) for (l, fn) in get_filenames(letters_pattern)}

    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates(min_scale=MIN_SCALE, max_scale=MAX_SCALE, scale_steps=SCALE_STEPS):
    rack_pattern = 'templates/rack/[A-Z].png'

    return {l: load_images(fn, min_scale, max_scale, scale_steps) for (l, fn) in get_filenames(rack_pattern)}

def build_icon_templates(min_scale=MIN_SCALE, max_scale=MAX_SCALE, scale_steps=SCALE_STEPS):
    icon_pattern = 'templates/*.png'

    return {l: load_images(fn, min_scale, max_scale, scale_steps) for (l, fn) in get_filenames(icon_pattern)}
