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
        self.group_state = None
        self.access_token = None
        self.auth_header = None

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
        r = requests.get(self.service + "/users/me/groups", headers=self.auth_header)
        json_object = json.loads(r.text)
        self.p_light_groups = json_object['data']
        return self.p_light_groups

    def group_state(self):
        pass

    def change_group_state(self, powered, brightness, lights):
        state_string = {'desired_state': {'brightness': brightness, 'powered': powered}}
        for group_id in lights:
            requests.post(self.service + "/groups/" + group_id + "/activate", json=state_string, headers=self.auth_header)
