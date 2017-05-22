from machine import UART
import ubinascii
import network

class BaseSonoffDevice():
    def __init__(self,ssid,psk,devmap):
        self.ssid = ssid
        self.psk = psk
        self.devmap = devmap
        self.wlan = network.WLAN(network.STA_IF)
        self.mac = self._get_mac()
        self.name = self._get_device_name()
        self.inputs = {}
        self.outputs = {}

    def connect_wlan(self):
        if not self.is_online:
            self.wlan.active(True)
            self.wlan.connect(self.ssid,self.psk)

    @property
    def is_online(self):
        return self.wlan.isconnected()

    def _get_device_name(self):
        return self.devmap[self.mac]

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
        TODO write in in a good way
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

# TODO: To be implemented
# Use machine.time_pulse_us(pin, pulse_level, timeout_us=1000000) to measure
# and filter pulses
#class SonoffSingle(BaseSonoffDevice):

# TODO. Make it a singleton to avoid possible class variable(octet) clash in
# case of improper usage
class DualRelay():
    """
    UART protocol description:

    Chip(power sequencer F330) sends current state of relays(NOT buttons!)
    on each button click.
    For example in case relay1 is turned on the button1 click will return
    x00.

    Byte sequence           R1 R2 R3 | Binary
    b'\xa0\x00\x00\xa1'     0  0  0  | 000
    b'\xa0\x00\x01\xa1'     1  0  0  | 100
    b'\xa0\x00\x02\xa1'     0  1  0  | 010
    b'\xa0\x00\xa1'         1  1  0  |
    b'\xa0\x00\x04\xa1'     0  0  1  | 001
    b'\xa0\x00\x07\xa1'     1  1  1  | 111
    ...

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
