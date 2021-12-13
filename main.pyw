import os
import subprocess
from subprocess import PIPE, run
import time

import requests
import win32api
import win32con
import win32gui_struct

try:
    import winxpgui as win32gui
except ImportError:
    import win32gui
from ctypes import *
import itertools, glob
from infi.systray import SysTrayIcon
import os
import ctypes

DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEQUERYREMOVE = 0x8001
DBT_DEVICEQUERYREMOVEFAILED = 0x8002
DBT_DEVICEMOVEPENDING = 0x8003
DBT_DEVICEREMOVECOMPLETE = 0x8004
DBT_DEVICETYPESSPECIFIC = 0x8005
DBT_CONFIGCHANGED = 0x0018

#
# type of device in DEV_BROADCAST_HDR
#
DBT_DEVTYP_OEM = 0x00000000
DBT_DEVTYP_DEVNODE = 0x00000001
DBT_DEVTYP_VOLUME = 0x00000002
DBT_DEVTYPE_PORT = 0x00000003
DBT_DEVTYPE_NET = 0x00000004

#
# media types in DBT_DEVTYP_VOLUME
#
DBTF_MEDIA = 0x0001
DBTF_NET = 0x0002

WORD = c_ushort
DWORD = c_ulong
defaultUSB = 1

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

def turnon(sysTrayIcon):
    global defaultUSB
    defaultUSB = 1


def turnoff(sysTrayIcon):
    global defaultUSB
    defaultUSB = 0


def QUIT(sysTrayIcon): print('Bye, then.')


def forceOpenUSB(sysTrayIcon):
    subprocess.call("adb shell input keyevent 82", startupinfo=si)
    time.sleep(0.1)
    subprocess.call("adb shell input text 1234", startupinfo=si)
    time.sleep(0.1)
    subprocess.call("adb shell input keyevent 66", startupinfo=si)
    time.sleep(2)
    forceUSBTether(sysTrayIcon)


def forceUSBTether(sysTrayIcon):
    global defaultUSB
    subprocess.call("adb shell svc usb setFunctions rndis", startupinfo=si)
    time.sleep(2)
    string = run("adb shell svc usb getFunctions", stdout=PIPE, stderr=PIPE, universal_newlines=True)
    time.sleep(0)
    if (not string.stderr.find('rndis')):
        subprocess.call("adb shell input keyevent 26", startupinfo=si)                                                          # Lock phone
        win32api.MessageBox(0, 'USB Tethering Succesfully TURNED ON', 'Success', 0x00001000)                                    # Alert
    defaultUSB = 1



class DEV_BROADCAST_HDR(Structure):
    _fields_ = [
        ("dbch_size", DWORD),
        ("dbch_devicetype", DWORD),
        ("dbch_reserved", DWORD)
    ]


class DEV_BROADCAST_VOLUME(Structure):
    _fields_ = [
        ("dbcv_size", DWORD),
        ("dbcv_devicetype", DWORD),
        ("dbcv_reserved", DWORD),
        ("dbcv_unitmask", DWORD),
        ("dbcv_flags", WORD)
    ]


def drive_from_mask(mask):
    n_drive = 0
    while 1:
        if (mask & (2 ** n_drive)):
            return n_drive
        else:
            n_drive += 1


class Notification:

    def __init__(self):
        message_map = {
            win32con.WM_DEVICECHANGE: self.onDeviceChange
        }

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "DeviceChangeDemo"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(
            classAtom,
            "Device Change Demo",
            style,
            0, 0,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0,
            hinst, None
        )

    def onDeviceChange(self, hwnd, msg, wparam, lparam):
        #
        # WM_DEVICECHANGE:
        #  wParam - type of change: arrival, removal etc.
        #  lParam - what's changed?
        #    if it's a volume then...
        #  lParam - what's changed more exactly
        #
        dev_broadcast_hdr = DEV_BROADCAST_HDR.from_address(lparam)
        global defaultUSB
        if wparam == DBT_DEVICEARRIVAL and defaultUSB == 1:


            dev_broadcast_hdr = DEV_BROADCAST_HDR.from_address(lparam)
            try:  # Check for internet connection
                request = requests.get('https://www.google.com', timeout=5)
                print('Connected')
            except(requests.ConnectionError, requests.Timeout):  # No Connection found
                defaultUSB = 0
                forceOpenUSB(systray)
            return 1





icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
menu_options = (

                ('Automatic Enabler', "tick.ico", (('Yes', "tick.ico", turnon),
                                                    ('No', None, turnoff),)),
                ('Force USB Tethering', None, forceUSBTether),
                ('Force Open and USB Tethering', None, forceOpenUSB),

)
systray = SysTrayIcon(icon_path, "USB Tethrering Enabler", menu_options, on_quit=QUIT, default_menu_index=1)
systray.start()
w = Notification()
win32gui.PumpMessages()

