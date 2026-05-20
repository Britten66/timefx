# TimeFX

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

## Requirements

- MSI motherboard with Mystic Light support
- MSI Center installed and open
- Python 3.10+ (64-bit)
- Run as Administrator

## Install

```
pip install -r requirements.txt
```

Double click `start.bat` to launch. It auto-elevates to Administrator.

## Color palette

| Period | Time | Colors |
|--------|------|--------|
| Night | 12:00 AM - 3:30 AM | Deep navy |
| Pre-Dawn | 4:00 AM - 4:30 AM | Blue-purple |
| Dawn | 5:00 AM - 5:30 AM | Rose, amber-rose |
| Sunrise | 6:00 AM - 6:30 AM | Deep orange |
| Morning | 7:00 AM - 8:00 AM | Warm gold |
| Mid Morning | 8:30 AM - 9:30 AM | Warm white to blue-white |
| Midday | 10:00 AM - 12:30 PM | Cool sky white |
| Afternoon | 1:00 PM - 3:30 PM | Warming amber |
| Golden Hour | 4:00 PM - 5:00 PM | Gold to deep amber |
| Sunset | 5:30 PM - 6:30 PM | Orange to red |
| Dusk | 7:00 PM - 8:30 PM | Red-purple to deep purple |
| Late Evening | 9:00 PM - 9:30 PM | Dark purple |
| Night | 10:00 PM - 11:30 PM | Dark navy |

## License

MIT

