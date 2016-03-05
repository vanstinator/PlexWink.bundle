from Automation import Automation
from qhue import Bridge
from qhue import QhueException

class PhilipsHueAutomation(Automation):
    """
    Class provides an abstract instance of Automation to interface with the Philips Hue service.
    """

    def __init__(self, hub_ip, username):

        self.username = "OVnUOPZnbLkOz7XpPAp6J5obGg0zkYbq1fLeedC0"
        self.hub_ip = hub_ip

        self.p_light_groups = None
        self.bridge = None
        self.authenticate()
        self.p_name = "Hue" # This cannot change going forward. There are quite a few things keying off this name

    @property
    def name(self):
        return self.p_name

    def is_authenticated(self):
        try:
            self.bridge()
            return True
        except QhueException:
            return False

    def authenticate(self):
        self.bridge = Bridge(self.hub_ip, self.username)

    def light_groups(self):
        self.p_light_groups = list()
        groups = self.bridge.groups()
        for group_id in groups:
            g = dict()
            if groups[group_id]['lights']:
                g['name'] = groups[group_id]['name']
                g['id'] = group_id
                self.p_light_groups.append(g)
        return self.p_light_groups

    @property
    def group_state(self, **kwargs):
        """
        Function will return the state of the group

        :return:
        """
        raise NotImplementedError("Must implement abstract method")

    def change_group_state(self, **kwargs):
        """
        Function will change the state of the selected light group and return boolean successful.

        :param kwargs:
        :return: boolean
        """
        raise NotImplementedError("Must implement abstract method")