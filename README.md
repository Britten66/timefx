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
