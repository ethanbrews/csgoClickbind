from ahk import AHK, Hotkey
from pynput import keyboard
from time import sleep
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import os

##### CONFIG #####

BIND_TRIGGER_KEY = '~$LButton'
TOGGLE_KEY = keyboard.Key.f8
ALLOW_IN_PROGRAMS = ("Counter-Strike: Global Offensive", "Valorant")
WINDOW_FOCUS_POLLING_TIME = 1 # Time in secs

### END CONFIG ###

is_bind_user_enabled = True
is_program_in_focus = False
is_closing = False

ahk = AHK()

def get_foreground_window_title() -> Optional[str]:
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1) # +1 to include null terminator in string
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)

    return buf.value if buf.value else None

def window_focus_detect_loop():
    global is_program_in_focus
    while not is_closing:
        window_name = get_foreground_window_title()
        tmp = window_name in ALLOW_IN_PROGRAMS
        re_eval = tmp != is_program_in_focus
        is_program_in_focus = tmp
        if re_eval:
            on_press(None)  # Make it re-evaluate
        sleep(WINDOW_FOCUS_POLLING_TIME)

# pynput handler
def on_press(key):
    global is_bind_user_enabled, is_program_in_focus
    if key == TOGGLE_KEY:
        is_bind_user_enabled = not is_bind_user_enabled

    start_script() if (is_bind_user_enabled and is_program_in_focus) else stop_script()

hotkey = Hotkey(
    ahk,
    BIND_TRIGGER_KEY,
    '''
    While GetKeyState("LButton","P"){
        if !GetKeyState("RControl", "P") {
            MouseClick, Left
            Sleep 10
        }
    }
    return
    ''')

def beep_turn_on():
    def inner():
            ahk.sound_beep(frequency=440, duration=50)
            ahk.sound_beep(frequency=620, duration=50)
            ahk.sound_beep(frequency=800, duration=50)
    threading.Thread(target=inner).start()
    

def beep_turn_off():
    def inner():
        if not is_bind_user_enabled:
            ahk.sound_beep(frequency=800, duration=30)
            ahk.sound_beep(frequency=620, duration=30)
            ahk.sound_beep(frequency=800, duration=30)
            ahk.sound_beep(frequency=440, duration=30)
            for _ in range(2):
                sleep(0.02)
                ahk.sound_beep(frequency=440, duration=30)
        else:
            ahk.sound_beep(frequency=800, duration=50)
            ahk.sound_beep(frequency=620, duration=50)
            ahk.sound_beep(frequency=440, duration=50)
    threading.Thread(target=inner).start()


def start_script():
    if not hotkey.running:
        hotkey.start()
        beep_turn_on()
        print("Clickbind Enabled"+(" "*16), end="\r")

def stop_script():
    if hotkey.running:
        hotkey.stop()
        beep_turn_off()
        print("Clickbind Disabled"+(" "*16), end="\r")



if __name__ == "__main__":
    listener = keyboard.Listener(
        on_press=on_press)
    listener.start()
    t = threading.Thread(target=window_focus_detect_loop)
    t.start()
    print("Starting Key listener for %s" % str(TOGGLE_KEY))
    print("Starting window focus listener")
    print("WARNING: If you don't close via ctrl+C, the auto hot key script may still be running and must be closed from the task bar!")
    print("Press ctrl+C to exit")
    print()
    print('Clickbind will enable when an allowed app is in focus', end='\r')
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        pass
    
    is_closing = True
    stop_script()
    os.system('TASKKILL /IM AutoHotkey.exe /F')
    print("Closed app")