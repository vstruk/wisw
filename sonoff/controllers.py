from machine import Timer
from utime import time
from .solidmqtt import SolidMQTTClient as MQTTClient
from .helpers import Lock
from .iotmanager import IotManager

# Controller base class
# Used by both Single and Dual
class Controller():
    def __init__(self,sonoff,broker):
        self.sonoff = sonoff
        self.devname = sonoff.name
        self.inputs = sonoff.inputs
        self.outputs = sonoff.outputs
        self.mqtt = MQTTClient(self.devname,broker)

        # Techincally timers are interrupts.
        # Using set/unset flags within the interrupts and then process them
        # in the main cycle as recommended
        self.mqtt_retry = Lock(False)
        self.health_pub = Lock()

        self.mqtt_init()

        self.reinit_timer = Timer(-1) # Reconnect to the borker and re-init mqtt
                                      # Timer prevents flooding in case the
                                      # network is up but broker is down

        self.health_timer = Timer(-1) # Publishing service health, i.e. uptime

        self.reinit_timer.init(period=1000,
                               mode=Timer.PERIODIC,
                               # Can't avoid lamdas
                               # here because of callback implementation
                               callback=lambda l: self.mqtt_retry.unlock())
        self.health_timer.init(period=5000,
                               mode=Timer.PERIODIC,
                               callback = lambda l: self.health_pub.unlock())

    def mqtt_init(self):
        if not self.mqtt_retry.is_locked():
            self.mqtt_retry.lock()
            if self.mqtt.failsafe_connect():
                self.mqtt.set_callback(self.mqtt_callback)
                self.mqtt_subscribe()
                self.publish_all()

    def publish_health(self):
        if not self.health_pub.is_locked():
            self.health_pub.lock()
            return   self.mqtt.publish(IotManager.get_device_topic(self.devname),
                              '{{uptime:{}}}'.format(time()),
                              qos=1
                              )
        return True


    def publish_all(self):
        for cname in self.outputs:
            self.publish_state(cname)

    def mqtt_subscribe(self):
        for cname in self.outputs:
            self.mqtt.subscribe(
                      IotManager.get_control_topic(self.devname, cname)
                                )

    def mqtt_callback(self,topic,msg):
        for cname,device in self.outputs.items():
            if topic == IotManager.get_control_topic(self.devname,cname):
                if msg == IotManager.get_control_value(True):
                    device.high()
                if msg == IotManager.get_control_value(False):
                    device.low()
                self.publish_state(cname)
                self.sonoff.write_uart()

    def publish_state(self,control):
        return self.mqtt.publish(
            IotManager.get_state_topic(self.devname,control),
            IotManager.get_state_value(self.outputs[control].state),
            retain=True, # Keep status messages persistent
            qos=1        # so any recently connected client app
            )            # could get the status


class SonoffDualController(Controller):
    def process(self):

        # socket.read in non-blocking mode at mqtt.check_msg()
        # returns None(instead of '') in some cases(see mqtt implementation)
        # so publish_health() also works as an additional 'ping'
        if not self.mqtt.check_msg() or not self.publish_health():
            self.mqtt_init()

        #Update mqtt status topic on change only
        if self.sonoff.check_uart():
            self.publish_all()

# TODO: to be implemented
#class SonoffSingleController(Controller):
