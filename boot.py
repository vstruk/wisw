# This file executes on every boot (including wake-boot from deepsleep)
import gc
import webrepl
import network

webrepl.start()

# Disable access point interface
ap = network.WLAN(network.AP_IF)
ap.active(False)
