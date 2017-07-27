from machine import UART,Pin
import ubinascii
import network
from .lock import Lock
from machine import Timer

class BaseSonoffDevice():
    def __init__(self,ssid,psk,settings):
        self.ssid = ssid
        self.psk = psk
        self.wlan = network.WLAN(network.STA_IF)
        self.mac = self._get_mac()
        self.settings = settings[self.mac]
        self.name = self.settings['name']
        self.inputs = {}
        self.outputs = {}
        self.dht = None

        pin = self.settings.get('dht22_pin')
        if pin:
            self.dht=DHTSensor(pin)

    def connect_wlan(self):
        if not self.is_online:
            self.wlan.active(True)
            self.wlan.connect(self.ssid,self.psk)

    @property
    def is_online(self):
        return self.wlan.isconnected()

    def _get_mac(self):
        return ubinascii.hexlify(self.wlan.config('mac'),':').decode()


class SonoffDualDevice(BaseSonoffDevice):

    def __init__(self,*args,**kwargs):
        super(SonoffDualDevice,self).__init__(*args,**kwargs)

        self.relay_class = DualRelay

        self.uart = UART(0, 19200)
        self.uart.init(19200, bits=8, parity=None, stop=1)

        for n in [0,1]:
            self.outputs['relay_{}'.format(n+1)] = self.relay_class(n)

    def check_uart(self):
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

    def write_uart(self):
        self.uart.write(self.relay_class.MSG_HEAD
                        + bytes((self.relay_class.octet,))
                        + self.relay_class.MSG_TAIL)

class SonoffSingleDevice(BaseSonoffDevice):
# TODO:
# Use machine.time_pulse_us(pin, pulse_level, timeout_us=1000000) to measure
# and filter pulses
    def __init__(self):
        raise NotImplementedError

class DHTSensor():
    """
    DHT22 humidity and temperature sensor
    """
    def __init__(self,pin):
        import dht

        self.remeasure = Lock()
        self.measure_timer = Timer(-1) # Temperature and humidity measure interval
        self.measure_timer.init(period=2000,
                               mode=Timer.PERIODIC,
                               callback = lambda l: self.remeasure.unlock())

        self.sensor = dht.DHT22(Pin(pin))

    def measure(self):
        if not self.remeasure.is_locked():
            try:
                self.sensor.measure()
            except OSError:
                pass
            self.remeasure.lock()

    def humidity(self):
        self.measure()
        return self.sensor.humidity()

    def temperature(self):
        self.measure()
        return self.sensor.temperature()


# TODO. Make it a singleton to avoid possible class variable(octet) clash in
# case of improper usage
class DualRelay():
    """
    UART protocol description:

    Chip(power sequencer F330) sends current state of relays(NOT buttons!)
    on each button click.
    For example in case relay1 is turned on the button1 click will return
    x00.

    Byte sequence           R1 R2 U  | Binary
    b'\xa0\x00\x00\xa1'     0  0  0  | 000
    b'\xa0\x00\x01\xa1'     1  0  0  | 100
    b'\xa0\x00\x02\xa1'     0  1  0  | 010
    b'\xa0\x00\xa1'         1  1  0  |
    b'\xa0\x00\x04\xa1'     0  0  1  | 001
    b'\xa0\x00\x07\xa1'     1  1  1  | 111
    ...

    R1,2 - Relays
    U    - Unused bit

    """

    MSG_HEAD=bytes((0xa0, 0x04))
    MSG_TAIL=bytes((0xa1, ))
    MSG_START=bytes((MSG_HEAD[0],))

    octet = 0 # The entire octet to send (MSG_HEAD[1,2] + octet + MSG_TAIL)
               # Contains state of both relays.
               # Using integer because there's no bitwise operations defined
               # on 'bytes' type.
    def __init__(self,bit):

        self.bit=bit

    def high(self):
        DualRelay.octet = DualRelay.octet | (1 << self.bit)

    def low(self):
        # Special case handling:  "0xa1(0b11) -> unset a bit" transition
        if DualRelay.octet == 0xa1:
            DualRelay.octet = 3 & (~ (1 << self.bit))
        else:
            DualRelay.octet = DualRelay.octet & (~ (1 << self.bit))

    @property
    def state(self):
        # Special case handling
        # for output states: '110' and '111'
        if DualRelay.octet == 0xa1 or DualRelay.octet == 0x07:
            return True
        return bool(DualRelay.octet & (1 << self.bit))
