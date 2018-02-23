#!/usr/bin/env python
import cv2
import os
import os.path
import glob

def filename_without_ext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def load_images(pattern):
    return [(filename_without_ext(f), f) for f in glob.glob(pattern)]

def build_templates():
    bonuses_pattern = 'templates/bonuses/*.png'
    letters_pattern = 'templates/letters/[A-Z].png'

    bonuses = {l: cv2.imread(fn, 0) for (l, fn) in load_images(bonuses_pattern)}
    letters = {l: cv2.imread(fn, 0) for (l, fn) in load_images(letters_pattern)}

    return { k: v for d in [bonuses, letters] for k, v in d.items() }

def build_rack_templates():
    rack_pattern = 'templates/rack/[A-Z].png'

    return {l: cv2.imread(fn, 0) for (l, fn) in load_images(rack_pattern)}

def build_icon_templates():
    icon_pattern = 'templates/*.png'

    return {l: cv2.imread(fn, 0) for (l, fn) in load_images(icon_pattern)}
