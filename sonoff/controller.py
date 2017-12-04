from machine import Timer
from utime import time
from .solidmqtt import SolidMQTTClient as MQTTClient
from .iotmanager import IotManager
from .lock import Lock


class Controller():
    """
    Controller base class
    Inherited by both SonoffSingleController and SonoffDualController
    It's an abstract class but Micropython has no abc module
    """
    def __init__(self,sonoff,broker):
        self.sonoff = sonoff
        self.devname = sonoff.name
        self.inputs = sonoff.inputs
        self.outputs = sonoff.outputs

        # Assume DHCP provides a DNS server
        # Not really want to handle this corner case
        dns=sonoff.wlan.ifconfig()[3] # (ip,mask,gw,dns)
        self.mqtt = MQTTClient(self.devname,broker,dns=dns)

        # Technically timers are interrupts.
        # Using set/unset flags within the interrupts and leaving them ASAP.
        # Process flags in the main cycle as recommended by micropython guide.
        self.mqtt_retry = Lock(False)
        self.report_pub = Lock()

        self.mqtt_init()

        self.reinit_timer = Timer(-1) # Reconnect to the borker and re-init mqtt
                                      # Timer prevents flooding in case the
                                      # network is up but broker is down.

        self.report_timer = Timer(-1) # Publishing reports, i.e. uptime,
                                      # temperature,humidity

        self.reinit_timer.init(period=5000, mode=Timer.PERIODIC,
                               callback=self.mqtt_retry.unlock)

        self.report_timer.init(period=5000, mode=Timer.PERIODIC,
                               callback=self.report_pub.unlock)

    def mqtt_init(self):
        if not self.mqtt_retry.is_locked():
            self.mqtt_retry.lock()
            if self.mqtt.failsafe_connect():
                self.mqtt.set_callback(self.mqtt_callback)
                self.mqtt_subscribe()
                self.publish_all()

    def publish_report(self):

        if not self.report_pub.is_locked():

            report = {}
            report['hostname']= self.devname
            report['uptime'] = time()

            if self.sonoff.dht:
                report['humidity'] = self.sonoff.dht.humidity()
                report['temperature'] = self.sonoff.dht.temperature()


            self.report_pub.lock()

            # We don't use ujson module to save memory
            # The only thing we need is s/'/"/
            return self.mqtt.publish(IotManager.get_device_topic(self.devname),
                                     str(report).replace("'", '"'),
                                     qos = 0)

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
        for relay_name,relay_class in self.outputs.items():
            if topic == IotManager.get_control_topic(self.devname,relay_name):
                if msg == IotManager.get_control_value(True):
                    relay_class.high()
                if msg == IotManager.get_control_value(False):
                    relay_class.low()
                self.publish_state(relay_name)
                self.sonoff.write_outputs()

    def publish_state(self,control):
        return self.mqtt.publish(
            IotManager.get_state_topic(self.devname,control),
            IotManager.get_state_value(self.outputs[control].state),
            retain=True, # Keep status messages persistent
            qos=0        # so any recently connected client app
            )            # could get the status

    def process(self):

        # socket.read in non-blocking mode at mqtt.check_msg()
        # returns None(instead of '') in some cases(see mqtt implementation)
        # so publish_report() also works as an additional 'ping'
        if not self.mqtt.check_msg() or not self.publish_report():
            self.mqtt_init()

        #Update mqtt status topic on change only
        if self.sonoff.check_inputs():
            self.publish_all()

