# TODO Calculate all the values(str.encode()) once on class init.
# Current implementation is suboptimal.

class IotManager():
    """ The class provides topics compatible with IoTManager[1] for publishing
    and reading.
    The idea is to make architecture pluggable and make it easy to replace this
    class with another implementation for another client.
    [1] https://play.google.com/store/apps/details?id=ru.esp8266.iotmanager
    """

    # TODO Does it make sense to rewrite it in setter-getter style?

    @staticmethod
    def get_state_topic(device,control):
        """
        Args:
            device (str)
            control (str)
        Returns:
            byte
        """
        return str.encode('/IoTmanager/{}/{}/status'.format(device,control))

    @staticmethod
    def get_state_value(state):
        """
        Args:
            state(bool)
        Returns:
            byte
        """
        return str.encode('{{\"status\":{}}}'.format(state*1))

    @staticmethod
    def get_control_topic(device,control):
        """
        Args:
            device (str)
            control (str)
        Returns:
            byte
        """
        return str.encode('/IoTmanager/{}/{}/control'.format(device,control))

    @staticmethod
    def get_control_value(state):
        """
        Args:
            state(bool)
        Returns:
            byte
        """
        return str.encode('{}'.format(state*1))

    @staticmethod
    def get_device_topic(device):
        """
        Args:
            device (str)
        Returns:
            byte
        """
        return str.encode('/IoTmanager/{}/uptime'.format(device))
