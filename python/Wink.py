# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Justin Vanderhooft
# Date: October 19, 2015
# Version 1.2.0

import requests
import json
import config
import time


class Wink:

    def __init__(self):
        print("Initializing Wink class")
        print("-Getting Token")
        global ACCESS_TOKEN, LIGHT_GROUPS
        ACCESS_TOKEN = self.get_wink_token()
        LIGHT_GROUPS = self.get_wink_light_groups()

    def get_wink_token(self):
        auth_string = {'client_id': config.WINK_CLIENT_ID, 'client_secret': config.WINK_CLIENT_SECRET,
                       'username': config.WINK_USERNAME, 'password': config.WINK_PASSWORD,
                       'grant_type': 'password'}

        r = requests.post("https://winkapi.quirky.com/oauth2/token/", json=auth_string);

        data = json.loads(r.text)

        return data['access_token']

    def get_wink_light_groups(self):
        array = []
        headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
        r = requests.get("https://winkapi.quirky.com/users/me/groups", headers=headers);
        json_object = json.loads(r.text)

        for group in json_object['data']:
            for local_group in config.WINK_ACTION_GROUPS:
                if group['name'] == local_group:
                    array.append(group['group_id'])

        return array

    def update_light_state(self, powered, brightness):
        headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
        state_string = {'desired_state': {'brightness': brightness, 'powered': powered}};
        for group_id in LIGHT_GROUPS:
            print(time.strftime("%I:%M:%S") + " - changing light group %s powered state to %s and brightness state to %s" % (group_id, "ON" if powered else "OFF", "DIM" if brightness == 0 else "FULL"));
            requests.post("https://winkapi.quirky.com/groups/" + group_id + "/activate", json=state_string,headers=headers);