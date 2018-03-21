#!/usr/bin/env python
import cv2
import numpy as np
import os
import os.path
import glob

def filename_without_ext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def get_filenames(pattern):
    return [(filename_without_ext(f), f) for f in glob.glob(pattern)]

def load_images(filename, min_scale=0.5, max_scale=1.5, scale_steps=17):
    image = cv2.imread(filename, 0)

    images = [image]

    for scale in np.linspace(min_scale, max_scale, scale_steps):
        images.append(cv2.resize(image, None, fx=scale, fy=scale))

    return images

def build_templates():
    bonuses_pattern = 'templates/bonuses/*.png'
    letters_pattern = 'templates/letters/[A-Z].png'

    bonuses = {l: load_images(fn) for (l, fn) in get_filenames(bonuses_pattern)}
    letters = {l: load_images(fn) for (l, fn) in get_filenames(letters_pattern)}

    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates():
    rack_pattern = 'templates/rack/[A-Z].png'

    return {l: load_images(fn) for (l, fn) in get_filenames(rack_pattern)}

def build_icon_templates():
    icon_pattern = 'templates/*.png'

    return {l: load_images(fn) for (l, fn) in get_filenames(icon_pattern)}
