from ahk import AHK, Hotkey
from pynput import keyboard
from time import sleep
from typing import Optional
from ctypes import wintypes, windll, create_unicode_buffer
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

##### CONFIG #####

BIND_TRIGGER_KEY = '~$LButton'
TOGGLE_KEY = keyboard.Key.f8
SERVER_ADDRESS = ('', 3001)
ALLOWED_PHASES = ("live", "over")
ALLOW_IN_PROGRAMS = ("Counter-Strike: Global Offensive", )
WINDOW_FOCUS_POLLING_TIME = 1 # Time in secs

WEAPONS_WITH_AUTO_FIRE_ENABLED = ["weapon_%s" % i for i in [
    "glock",
    "elite",
    "p250",
    "tec9",
    #"deagle",
    #"cz75a",
    "usp_silencer",
    #"revolver",
    "hkp2000",
    "fiveseven",

    "nova",
    "xm1014",
    "sawedoff",
    "mag7"
]]

### END CONFIG ###

is_bind_user_enabled = True
is_program_in_focus = False
is_closing = False

_last_selected_weapon = None
_last_phase = None

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
            _last_phase = None # Force re-evaluation of whether script is enabled
        sleep(WINDOW_FOCUS_POLLING_TIME)

# pynput handler
def on_press(key):
    global _last_phase, _last_selected_weapon, is_bind_user_enabled
    if key == TOGGLE_KEY:
        is_bind_user_enabled = not is_bind_user_enabled
    if is_bind_user_enabled:
        t1, t2 = _last_phase, _last_selected_weapon
        _last_phase, _last_selected_weapon = None, None
        auto_start_stop_script(t1, t2)
    else:
        stop_script()

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
        ahk.sound_beep(frequency=500, duration=100)
        ahk.sound_beep(frequency=800, duration=100)
    threading.Thread(target=inner).start()
    

def beep_turn_off():
    def inner():
        if not is_bind_user_enabled:
            ahk.sound_beep(frequency=1000, duration=100)
        ahk.sound_beep(frequency=800, duration=100)
        ahk.sound_beep(frequency=500, duration=100)
    threading.Thread(target=inner).start()

def auto_start_stop_script(phase: str, weapon: str):
    global _last_phase, _last_selected_weapon, is_bind_user_enabled, is_program_in_focus
    if _last_phase == phase and _last_selected_weapon == weapon:
        return
    
    _last_phase = phase
    _last_selected_weapon = weapon

    print(f"Evaluating phase={phase}, weapon={weapon}, user_enabled={is_bind_user_enabled}, focus={is_program_in_focus}")

    if phase not in ALLOWED_PHASES or not is_program_in_focus:
        stop_script()
        return

    if weapon in WEAPONS_WITH_AUTO_FIRE_ENABLED and is_bind_user_enabled:
        start_script()
    else:
        stop_script()


def start_script():
    if not hotkey.running:
        hotkey.start()
        beep_turn_on()
        print("Clickbind Enabled")

def stop_script():
    if hotkey.running:
        hotkey.stop()
        beep_turn_off()
        print("Clickbind Disabled")


class MyRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_request(self, code=None, size=None):
        pass
    
    def do_POST(self):
        self.send_header('Content-type', 'text/html')
        self.send_response(200)
        self.end_headers()
        
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode('utf-8')

        payload: dict = json.loads(body)

        try:
            phase = payload["round"]["phase"]
            _weapons = payload["player"]["weapons"]
        except KeyError:
            print("KeyError: phase or _weapons is NoneType")
            return

        if phase is None or _weapons is None:
            print("debug phase or weapons is NoneType")
            return

        selected_weapon = list(filter( lambda x: x["state"] == "active", [_weapons.get("weapon_0", {"state": ""}), _weapons.get("weapon_1", {"state": ""}), _weapons.get("weapon_2", {"state": ""})]))[0]["name"]
        auto_start_stop_script(phase, selected_weapon)


def run(server_class=HTTPServer, handler_class=MyRequestHandler):
    httpd = server_class(SERVER_ADDRESS, handler_class)
    httpd.serve_forever()


if __name__ == "__main__":
    listener = keyboard.Listener(
        on_press=on_press)
    listener.start()
    t = threading.Thread(target=window_focus_detect_loop)
    t.start()
    print("Starting Key listener for %s" % str(TOGGLE_KEY))
    print("Starting window focus listener")
    print("Starting HTTP server at %s:%s" % (SERVER_ADDRESS[0] if SERVER_ADDRESS[0] != "" else "127.0.0.1", SERVER_ADDRESS[1]))
    print("Press ctrl+C to exit")
    try:
        run()
    except KeyboardInterrupt:
        pass
    
    is_closing = True
    hotkey.stop()
    print("Closed app")