from sys import print_exception
from sonoff.sonoff import SonoffSingle,SonoffDual
from sonoff.controller import Controller
from sonoff.sonoff import BaseSonoff
from config import SSID,PSK,BROKER,SETTINGS,WEBREPL_PASSWORD
import webrepl
import time

webrepl.start(password=WEBREPL_PASSWORD)

# Selecting a class according to the device type
# It made simple as the Factory pattern seems like overkill for a single class
CLASS_MAP = {'dual':   SonoffDual,
             'single': SonoffSingle
            }

device_class = CLASS_MAP[SETTINGS[BaseSonoff.mac()]['type']]
device =device_class(SSID, PSK, SETTINGS[BaseSonoff.mac()])

controller = Controller(device, BROKER)

device.connect_wlan()

while True:

    try:
      time.sleep_ms(100)
      controller.process()

      """
      (Applies to SonoffDual)
      Due to hardware restrictions we use the same UART as the REPL.
      Data sent via UART may contain keyboard interrupt sequence so we have
      to handle it.
      """
    except KeyboardInterrupt:
        pass

    except Exception as e:
        exc = e # Use it to check what happened if runtime raised exception.
                # Connect to web REPL and execute: print_exception(exc)
        raise e
