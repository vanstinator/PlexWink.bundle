from Automation import Automation
import requests
import json


class WinkAutomation(Automation):
    """
    Class provides an abstract instance of Automation to interface with the Wink service.
    """

    def __init__(self, client_id, client_secret, username, password):

        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.service = "https://winkapi.quirky.com"

        self.p_light_groups = None
        self.access_token = None
        self.auth_header = None
        self.authenticate()
        self.p_name = "Wink" # This cannot change going forward. There are quite a few things keying off this name

    @property
    def name(self):
        return self.p_name

    def is_authenticated(self):
        if self.access_token:
            return True
        return False

    def authenticate(self):
        auth_string = {'client_id': self.client_id,
                       'client_secret': self.client_secret,
                       'username': self.username,
                       'password': self.password,
                       'grant_type': 'password'}

        r = requests.post(self.service + "/oauth2/token/", json=auth_string)

        data = json.loads(r.text)
        self.access_token = data['access_token']
        self.auth_header = {'Authorization': 'Bearer ' + self.access_token}

    def light_groups(self):
        """
        Returns all the wink groups on a user account. Only returns non-empty groups
        :return: list[dict()]
        """
        self.p_light_groups = list()
        r = requests.get(self.service + "/users/me/groups", headers=self.auth_header)
        json_object = json.loads(r.text)
        for group in json_object['data']:
            g = dict()
            if group['members']:
                g['name'] = group['name']
                g['id'] = group['group_id']
                self.p_light_groups.append(g)
        return self.p_light_groups

    def change_group_state(self, lights, powered=False, dim=False):
        if dim:
            brightness = 0
        else:
            brightness = 100
        state_string = {'desired_state': {'brightness': brightness, 'powered': powered}}
        for group_id in lights:
            requests.post(self.service + "/groups/" + group_id + "/activate", json=state_string, headers=self.auth_header)
