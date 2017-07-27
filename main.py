from sys import print_exception
from sonoff.sonoff import SonoffDualDevice
from sonoff.controllers import SonoffDualController
import time
from config import *

device = SonoffDualDevice(SSID,PSK,SETTINGS)
device.connect_wlan()

controller = SonoffDualController(device,BROKER)

while True:

    try:
      time.sleep_ms(100)
      controller.process()

      """
      Due to hardware restrictions we use the same UART as the REPL.
      Data sent via UART may contain keyboard interrupt sequence so we have
      to handle it.
      """
    except KeyboardInterrupt:
        pass

    except Exception as e:
        exc = e # Use it to check what happened if runtime raised exception.
                # Connect to web REPL and execute: print_exception(exc)
