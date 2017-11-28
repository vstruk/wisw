from machine import Pin

class SingleRelay():
    def __init__(self):
        self.relay = Pin(12,Pin.OUT)

    def high(self):
        self.relay.value(True)

    def low(self):
        self.relay.value(False)

    def switch(self):
        self.relay.value(not self.relay.value())

    @property
    def state(self):
        return bool(self.relay.value())

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
