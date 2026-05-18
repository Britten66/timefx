"""
TimeFX - MSI Mystic Light

I built this while learning Python as a way to push my MSI motherboard LEDs
through a full day and night color cycle automatically. The idea was simple:
make the RGB on my board feel like the sky outside, shifting gradually from
deep navy at midnight through sunrise oranges and midday whites and back down
through golden hour and sunset reds into night again.

It reads the real world clock and maps it to a set of color keyframes I tuned
by hand. Every second it blends smoothly between them so there are no visible
jumps, just a slow natural drift.

The whole thing sits in the system tray with a colored circle that matches
whatever the LEDs are showing. Right click to disable or quit.

Requires MSI Center open and the script running as Administrator.
Uses mlsdk64.dll from the MSI Mystic Light SDK to talk directly to the hardware.
"""

import ctypes
import os
import sys
import threading
import time
import datetime

from ctypes.wintypes import DWORD
from comtypes import BSTR

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("Run: pip install pystray Pillow comtypes")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# How often the color recalculates - every second keeps transitions smooth
UPDATE_SEC = 1

# ---------------------------------------------------------------------------
# MSI SDK setup
# ctypes is like JNI in Java - it lets Python call into a native Windows DLL
# ---------------------------------------------------------------------------

# Tell Python where to find the DLL and its dependencies
os.add_dll_directory(SCRIPT_DIR)
os.add_dll_directory(r"C:\Program Files (x86)\MSI\MSI Center\Mystic Light")

# Load the MSI SDK DLL - this is the library that talks to the hardware
_dll = ctypes.CDLL(os.path.join(SCRIPT_DIR, "mlsdk64.dll"))

# Tell Python what arguments each function expects and what it returns
# Without this ctypes guesses wrong and the call crashes
_dll.MLAPI_Initialize.argtypes  = [];                _dll.MLAPI_Initialize.restype  = ctypes.c_int
_dll.MLAPI_SetLedStyle.argtypes = [BSTR,DWORD,BSTR]; _dll.MLAPI_SetLedStyle.restype = ctypes.c_int
_dll.MLAPI_SetLedColor.argtypes = [BSTR,DWORD,DWORD,DWORD,DWORD]
_dll.MLAPI_SetLedColor.restype  = ctypes.c_int

_sdk_ready = False

def init_sdk():
    global _sdk_ready
    ret = _dll.MLAPI_Initialize()
    if ret == 0:
        # Style must be Steady before SetLedColor works - learned this the hard way
        _dll.MLAPI_SetLedStyle(BSTR("MSI_MB"), 0, BSTR("Steady"))
        _sdk_ready = True
    return ret == 0

def set_hw_color(r: int, g: int, b: int):
    if not _sdk_ready:
        return
    # MSI_MB targets the motherboard, index 0 means all zones at once
    _dll.MLAPI_SetLedColor(BSTR("MSI_MB"), 0, r, g, b)

# ---------------------------------------------------------------------------
# Color keyframes
# Each entry is (hour, R, G, B, label)
# The script interpolates between these every second so there are no visible jumps
# 30 minute intervals give a natural gradual shift like watching the sky outside
# ---------------------------------------------------------------------------

KEYFRAMES = [
    # --- deep night ---
    ( 0.0,   6,   6,  48, "Night"),
    ( 0.5,   6,   6,  48, "Night"),
    ( 1.0,   5,   5,  45, "Night"),
    ( 1.5,   5,   5,  45, "Night"),
    ( 2.0,   5,   5,  44, "Night"),
    ( 2.5,   5,   5,  44, "Night"),
    ( 3.0,   5,   5,  46, "Night"),
    ( 3.5,   7,   5,  52, "Night"),
    # --- pre-dawn ---
    ( 4.0,  12,   6,  65, "Pre-Dawn"),
    ( 4.5,  28,  10,  72, "Pre-Dawn"),
    # --- dawn breaks ---
    ( 5.0,  90,  30,  50, "Dawn"),
    ( 5.5, 165,  58,  28, "Dawn"),
    # --- sunrise ---
    ( 6.0, 215, 100,  30, "Sunrise"),
    ( 6.5, 245, 140,  40, "Sunrise"),
    # --- morning ---
    ( 7.0, 255, 168,  52, "Morning"),
    ( 7.5, 255, 188,  80, "Morning"),
    ( 8.0, 255, 205, 115, "Morning"),
    ( 8.5, 240, 220, 175, "Mid Morning"),
    ( 9.0, 222, 228, 230, "Mid Morning"),
    ( 9.5, 215, 225, 240, "Mid Morning"),
    # --- midday ---
    (10.0, 210, 222, 252, "Midday"),
    (10.5, 205, 220, 255, "Midday"),
    (11.0, 200, 218, 255, "Midday"),
    (11.5, 202, 218, 255, "Midday"),
    (12.0, 205, 220, 255, "Midday"),
    (12.5, 205, 220, 252, "Midday"),
    # --- afternoon ---
    (13.0, 210, 220, 248, "Afternoon"),
    (13.5, 218, 220, 240, "Afternoon"),
    (14.0, 232, 220, 210, "Afternoon"),
    (14.5, 245, 218, 175, "Afternoon"),
    (15.0, 255, 210, 140, "Afternoon"),
    (15.5, 255, 200, 112, "Afternoon"),
    # --- golden hour ---
    (16.0, 255, 185,  80, "Golden Hour"),
    (16.5, 255, 168,  55, "Golden Hour"),
    (17.0, 255, 140,  30, "Golden Hour"),
    (17.5, 255, 108,  18, "Sunset"),
    # --- sunset ---
    (18.0, 245,  72,  14, "Sunset"),
    (18.5, 220,  45,  30, "Sunset"),
    (19.0, 185,  28,  65, "Dusk"),
    (19.5, 140,  18,  88, "Dusk"),
    # --- dusk ---
    (20.0,  90,  12, 105, "Dusk"),
    (20.5,  55,   8,  90, "Dusk"),
    (21.0,  30,   6,  72, "Late Evening"),
    (21.5,  16,   5,  60, "Late Evening"),
    # --- night ---
    (22.0,   9,   5,  52, "Night"),
    (22.5,   7,   5,  50, "Night"),
    (23.0,   6,   5,  48, "Night"),
    (23.5,   6,   5,  48, "Night"),
    (24.0,   6,   6,  48, "Night"),
]

# ---------------------------------------------------------------------------
# Color math
# ---------------------------------------------------------------------------

# Linear interpolation - blends between two values, same as Math.lerp in Java
# t is 0.0 to 1.0, where 0 is fully A and 1 is fully B
def lerp(a, b, t):
    return max(0, min(255, int(a + (b - a) * t)))

# Find which two keyframes the current hour falls between then blend between them
def color_for_hour(hour):
    hour = hour % 24
    for i in range(len(KEYFRAMES) - 1):
        h0, r0, g0, b0, _ = KEYFRAMES[i]
        h1, r1, g1, b1, _ = KEYFRAMES[i + 1]
        if h0 <= hour < h1:
            t = (hour - h0) / (h1 - h0)
            return lerp(r0,r1,t), lerp(g0,g1,t), lerp(b0,b1,t)
    return KEYFRAMES[0][1], KEYFRAMES[0][2], KEYFRAMES[0][3]

# Same logic but returns the period label instead of the color
def label_for_hour(hour):
    hour = hour % 24
    for i in range(len(KEYFRAMES) - 1):
        h0, *_, label = KEYFRAMES[i]
        h1 = KEYFRAMES[i + 1][0]
        if h0 <= hour < h1:
            return label
    return KEYFRAMES[0][4]

# Get the current real world time as a decimal hour - e.g. 14.5 = 2:30 PM
def real_hour():
    n = datetime.datetime.now()
    return n.hour + n.minute / 60 + n.second / 3600

# ---------------------------------------------------------------------------
# Shared state between threads
# Using a lock so the sync thread and tray thread don't read/write at the same time
# Same concept as synchronized blocks in Java
# ---------------------------------------------------------------------------
_state = {"enabled": True, "color": (10,10,60), "label": "starting"}
_lock  = threading.Lock()

# ---------------------------------------------------------------------------
# Main sync loop - runs on its own thread in the background
# ---------------------------------------------------------------------------
def sync_loop():
    last = None
    while True:
        with _lock:
            enabled = _state["enabled"]

        if enabled and _sdk_ready:
            h     = real_hour()
            color = color_for_hour(h)
            label = label_for_hour(h)

            with _lock:
                _state["color"] = color
                _state["label"] = label

            # Only send to hardware if the color actually changed
            if color != last:
                set_hw_color(*color)
                last = color

        time.sleep(UPDATE_SEC)

# ---------------------------------------------------------------------------
# Tray icon
# ---------------------------------------------------------------------------

# Draw a colored circle for the tray icon - shows current LED color at a glance
# Red X overlay when disabled
def make_icon(r, g, b, enabled=True):
    img  = Image.new("RGBA", (64,64), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    fill = (r,g,b,255) if enabled else (35,35,35,200)
    draw.ellipse([4,4,60,60], fill=fill)
    if not enabled:
        draw.line([14,14,50,50], fill=(180,0,0,255), width=5)
        draw.line([50,14,14,50], fill=(180,0,0,255), width=5)
    return img

def tray_title():
    with _lock:
        e, label = _state["enabled"], _state["label"]
    return f"TimeFX  |  {label}" if e else "TimeFX - disabled"

# Toggle on/off from the tray right-click menu
def on_toggle(icon, item):
    with _lock:
        _state["enabled"] = not _state["enabled"]
        enabled = _state["enabled"]
    if not enabled:
        set_hw_color(0, 0, 0)
    icon.update_menu()

# Turn off LEDs and exit cleanly
def on_quit(icon, item):
    set_hw_color(0, 0, 0)
    time.sleep(0.5)
    icon.stop()

# Label changes dynamically based on current state
def get_toggle_label(item):
    with _lock:
        return "Disable" if _state["enabled"] else "Enable"

# Runs on its own thread - updates the tray icon color every second to match the LEDs
def icon_updater(icon):
    while True:
        with _lock:
            r,g,b   = _state["color"]
            enabled = _state["enabled"]
        icon.icon  = make_icon(r, g, b, enabled)
        icon.title = tray_title()
        time.sleep(UPDATE_SEC)

# ---------------------------------------------------------------------------
def main():
    if not init_sdk():
        print("Could not connect to MSI Mystic Light service.")
        print("Make sure MSI Center is open and this script is running as Administrator.")
        input("Press Enter to exit.")
        sys.exit(1)

    print("MSI SDK connected. Starting tray icon...")

    # Sync loop runs in the background - same as a daemon thread in Java
    threading.Thread(target=sync_loop, daemon=True).start()

    icon = pystray.Icon(
        "TimeFX",
        icon=make_icon(10,10,60),
        title="TimeFX",
        menu=pystray.Menu(
            pystray.MenuItem(get_toggle_label, on_toggle, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        ),
    )

    # Icon updater also runs in the background
    threading.Thread(target=icon_updater, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    main()
