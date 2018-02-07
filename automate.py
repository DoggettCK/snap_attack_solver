#!/usr/bin/env python
import os
import re
import pywintypes
import win32gui
import win32ui
import win32con
import extract_text
from PIL import ImageGrab

WINDOW_TITLE = "Snap Attack"

def window_enumeration_handler(hwnd, windows):
    windows.append((hwnd, win32gui.GetWindowText(hwnd)))
    pass

def get_snap_attack_window():
    windows = []

    win32gui.EnumWindows(window_enumeration_handler, windows)

    return next((hwnd for (hwnd, title) in windows if re.search(WINDOW_TITLE, title)), None)

def take_snapshot(hwnd, pid):
    os.mkdirs('input', exist_ok=True)
    filename = "input/{}.png".format(pid)
    bounding_box = win32gui.GetWindowRect(hwnd)
    ImageGrab.grab(bounding_box).save(filename, "PNG")
    print("Saved snapshot to {}".format(filename))
    return filename

if __name__ == "__main__":
    hwnd = get_snap_attack_window()

    if hwnd == None:
        print("Unable to find SnapAttack window")
    else:
        win32gui.SetForegroundWindow(hwnd)
        screenshot = take_snapshot(hwnd, os.getpid())
        extract_text.process(screenshot, {'debug': True, 'scrape': True})

