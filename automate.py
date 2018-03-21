#!/usr/bin/env python
import os
import pywintypes
import win32gui
import win32ui
import win32con
import extract_text
import time
from PIL import ImageGrab

WINDOW_TITLE = "Snap Attack"

def window_enumeration_handler(hwnd, windows):
    windows.append((hwnd, win32gui.GetWindowText(hwnd)))
    pass

def get_snap_attack_window():
    windows = []

    win32gui.EnumWindows(window_enumeration_handler, windows)

    return next((hwnd for (hwnd, title) in windows if WINDOW_TITLE == title.strip()), None)

def take_snapshot(hwnd, pid):
    filename = "input/{}.png".format(pid)

    bounding_box = win32gui.GetWindowRect(hwnd)
    ImageGrab.grab(bounding_box).save(filename, "PNG")

    print("Saved snapshot to {}".format(filename))

    return filename

def setup():
    for directory in ['input', 'output', 'templates']:
        os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    setup()
    hwnd = get_snap_attack_window()

    if hwnd == None:
        print("Unable to find SnapAttack window")
    else:
        win32gui.ShowWindow(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        screenshot = take_snapshot(hwnd, os.getpid())
        extract_text.process(screenshot, {'debug': False, 'dry_run': False})
        os.remove(screenshot)

