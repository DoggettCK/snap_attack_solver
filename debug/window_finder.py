#!/usr/bin/env python

import win32gui
import win32api
import win32con
import win32process

EXE_NAME = 'Microsoft.WordamentTapSnap'
WIN_TITLE = 'Snap Attack'

def print_process_info(pid, hwnd, exe, title):
    print("Process ID: {}".format(pid))
    print("Window Handle: {}".format(hwnd))
    print("Executable: {}".format(exe))
    print("Title: {}".format(title))
    print("------------------")

def get_process_info(pid):
    try:
        hwnd = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
        exe = win32process.GetModuleFileNameEx(hwnd, 0)
        title = win32gui.GetWindowText(hwnd)

        return (pid, hwnd, exe, title)
    except:
        return None

def find_snap_attack_by_title():
    print("Finding by title")
    windows = []

    win32gui.EnumWindows(lambda hwnd, window_list: window_list.append((hwnd, win32gui.GetWindowText(hwnd))), windows)

    for hwnd, title in windows:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process_info = get_process_info(pid)

        if process_info is None:
            continue
        
        p_id, p_hwnd, p_exe, p_title = process_info

        if EXE_NAME in p_exe:
            print("Found by exe name")
            print_process_info(*process_info)
        elif WIN_TITLE in p_title:
            print("Found by window_title")
            print_process_info(*process_info)

def find_snap_attack_by_exe():
    print("Finding by exe")
    procs = win32process.EnumProcesses()
    for pid in procs:
        process_info = get_process_info(pid)

        if process_info is None:
            continue
        
        p_id, p_hwnd, p_exe, p_title = process_info

        if EXE_NAME in p_exe:
            print("Found by exe name")
            print_process_info(*process_info)
        elif WIN_TITLE in p_title:
            print("Found by window_title")
            print_process_info(*process_info)

if __name__ == "__main__":
    find_snap_attack_by_exe()
    find_snap_attack_by_title()
