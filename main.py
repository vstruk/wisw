from sonoff.sonoff import SonoffDual
from sonoff.controllers import SonoffDualController
import time
from config import *

device = SonoffDual(SSID,PSK,DEVMAP)

controller = SonoffDualController(device,BROKER)

while True:

    try:
        time.sleep_ms(100)
        controller.process()
    except KeyboardInterrupt: # Due to hardware restrictions we use the same
        pass                  # UART as the REPL. UART data exchange may contain
                              # keyboard interrupt sequence so we have to ignore
                              # them
