from umqtt.simple import MQTTClient
import usocket as socket

class SolidMQTTClient(MQTTClient):
    """ The device must be functional(hw button controlled) even in case
        a network and/or broker are down
        So it just keep trying to reconnect in a fail safe manner
     """

    def __init__(self, client_id, server,dns, port=0, user=None, password=None,
                 keepalive=0, ssl=False, ssl_params={}):
        # Copied from simple.mqtt and slightly modified
        # DNS query moved to failsafe_connect because we usually have no
        # network connectivity on the class init stage
        if port == 0:
            port = 8883 if ssl else 1883
        self.port = port
        self.server = server
        self.client_id = client_id
        self.sock = socket.socket()
        self.ssl = ssl
        self.ssl_params = ssl_params
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False
        self.dns = dns

    def failsafe_connect(self,*args,**kwargs):
        try:
            # Dirty hack:
            # getaddrinfo is a part of micropython and has no configurable
            # timeout. The default is too long
            # Check if DNS server is accessible before querying it or raise
            # OSError
            dns_sock = socket.socket()
            # Usually DNS queries are sent via UDP, but it's harder to check.
            # Assume the server listens TCP 53 as well. It should.
            dns_sock.connect((self.dns,53))
            dns_sock.close()

            self.addr = socket.getaddrinfo(self.server, self.port)[0][-1]
            self.connect(*args,**kwargs)
            self.sock.settimeout(2)
            return True
        except OSError:
            return False

    def publish(self,*args,**kwargs):
        try:
            super().publish(*args,**kwargs)
            return True
        except OSError:
            return False

    def check_msg(self):
        try:
            self.sock.setblocking(False)
            self.wait_msg()
            return True
        except OSError:
            return False
