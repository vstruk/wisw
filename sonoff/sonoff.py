from machine import UART,Pin
import ubinascii
import network
from .lock import Lock
from .dhtsensor import DHTSensor
from .relays import SingleRelay,DualRelay
from utime import ticks_diff,ticks_ms

class BaseSonoff():
    _mac = None

    def __init__(self,ssid,psk,settings):
        self.ssid = ssid
        self.psk = psk
        self.wlan = network.WLAN(network.STA_IF)
        self.settings = settings
        self.name = self.settings['name']
        self.type = self.settings['type']
        self.inputs = {}
        self.outputs = {}
        self.dht = None


        pin = self.settings.get('dht22_pin')
        if pin:
            self.dht=DHTSensor(pin)

    def connect_wlan(self):
        if not self.wlan.isconnected():
            self.wlan.active(True)
            self.wlan.connect(self.ssid,self.psk)

    @classmethod
    def mac(cls):
        if not cls._mac:
            cls._mac = ubinascii.hexlify(network.WLAN(network.STA_IF).config(
                'mac'),':').decode()
        return cls._mac


class SonoffDual(BaseSonoff):

    def __init__(self,*args,**kwargs):
        super(SonoffDual, self).__init__(*args, **kwargs)

        self.relay_class = DualRelay
        self.uart = UART(0, 19200)
        self.uart.init(19200, bits=8, parity=None, stop=1)

        for n in [0,1]:
            self.outputs['relay_{}'.format(n+1)] = self.relay_class(n)

    # read uart
    def check_inputs(self):
        """
        Reads uart and returns bool value if the relay state changed or not
        """
        msg = self.uart.read() # Returns None if no data received
        if len(msg or '') > 1:
            if len(msg) > 4 : # Means we have read a few byte sequences.
                              # Get the last one
             # TODO Edge case
             #What if .rfind returns '-1'= Not found?
             #Need to handle it. Just in case of wrong data
                msg = msg[msg.rfind(self.relay_class.MSG_START):]

            old = self.relay_class.octet
            self.relay_class.octet = msg[2]

            return (old != self.relay_class.octet)

        return False

    # write uart
    def write_outputs(self):
        self.uart.write(self.relay_class.MSG_HEAD
                        + bytes((self.relay_class.octet,))
                        + self.relay_class.MSG_TAIL)



class SonoffSingle(BaseSonoff):

    def __init__(self,*args,**kwargs):

        self.input_prev = False # previous input value
        super(SonoffSingle, self).__init__(*args, **kwargs)
        self.outputs['relay_0']=SingleRelay()

    @property
    def input(self):
        # The input is inverted
        return not Pin(0,Pin.IN).value()

    def check_inputs(self):

        input_changed = False

        if self.input and not self.input_prev:
            start = ticks_ms()
            while self.input:
                if ticks_diff(ticks_ms(),start) > 50:
                    self.outputs['relay_0'].switch()
                    input_changed = True
                    break

        self.input_prev = self.input
        return input_changed

    def write_outputs(self):
        pass

