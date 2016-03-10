from Automation import Automation
from qhue import Bridge
from qhue import create_new_username


class PhilipsHueAutomation(Automation):
    """
    Class provides an abstract instance of Automation to interface with the Philips Hue service.
    """

    def __init__(self, hub_ip):

        self.username = Data.Load("hue_username")
        self.hub_ip = hub_ip

        self.p_light_groups = None
        self.bridge = None
        self.authenticate()
        self.p_name = "Philips Hue" # This cannot change. There are quite a few things keying off this name

    @property
    def name(self):
        return self.p_name

    def has_username(self):
        if self.username:
            return True
        return False

    def is_authenticated(self):
        try:
            self.bridge()
            return True
        except:
            return False

    def authenticate(self):
        # Data.Save("hue_username", None)
        if not self.username:
            try:
                self.username = create_new_username(self.hub_ip)
            except:
                pass
            Data.Save("hue_username", self.username)
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

    def change_group_state(self, lights, powered=False, dim=False):
        if dim:
            brightness = 0
        else:
            brightness = 255

        for light in lights:
            Log(self.bridge.groups[light]())
            self.bridge.groups[light].action(on=powered, bri=brightness)
