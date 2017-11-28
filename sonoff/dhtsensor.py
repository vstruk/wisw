from .lock import Lock
from machine import Timer
import dht

class DHTSensor():
    """
    DHT22 humidity and temperature sensor
    """
    def __init__(self,pin):

        self.remeasure = Lock()
        self.measure_timer = Timer(-1) # Temperature and humidity measure interval
        self.measure_timer.init(period=2000, mode=Timer.PERIODIC,
                                callbac=self.remeasure.unlock)

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


