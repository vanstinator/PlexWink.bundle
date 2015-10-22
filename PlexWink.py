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
# Version 1.1.0

import requests
import json
from time import sleep
import xml.etree.ElementTree as ElementTree
import config

ACCESS_TOKEN = ''

CURRENT_STATUS = ''

def get_wink_token():
    auth_string = {'client_id': config.WINK_CLIENT_ID, 'client_secret': config.WINK_CLIENT_SECRET,
                   'username': config.WINK_USERNAME, 'password': config.WINK_PASSWORD,
                   'grant_type': 'password'}

    r = requests.post("https://winkapi.quirky.com/oauth2/token/", json=auth_string);

    data = json.loads(r.text)

    return data['access_token']


def get_wink_light_groups():
    global WINK_GROUP_IDS
    array = []
    headers = {'Authorization': 'Bearer ' + access_token}
    r = requests.get("https://winkapi.quirky.com/users/me/groups", headers=headers);
    json_object = json.loads(r.text)

    for group in json_object['data']:
        for local_group in config.WINK_ACTION_GROUPS:
            if group['name'] == local_group:
                array.append(group['group_id'])

    return array

def get_plex_token():
    auth = {'user[login]': config.PLEX_USERNAME, 'user[password]': config.PLEX_PASSWORD}
    headers = {'X-Plex-Client-Identifier': 'PlexWink'}
    r = requests.post('https://plex.tv/users/sign_in.json', params=auth, headers=headers)

    data = json.loads(r.text)

    return data['user']['authentication_token']


def is_plex_playing(plex_status):
    global CURRENT_STATUS
    for item in plex_status.findall('Video'):
        for client_name in config.PLEX_CLIENTS:
            if item.find('Player').get('title') == client_name:
                for username in config.PLEX_AUTHORIZED_USERS:
                    if item.find('User').get('title') == username:
                       if item.find('Player').get('state') == 'playing' and CURRENT_STATUS != item.find('Player').get('state'):
                            CURRENT_STATUS = item.find('Player').get('state')
                            return True;

    return False


def is_plex_paused(plex_status):
    global CURRENT_STATUS
    for item in plex_status.findall('Video'):
        for client_name in config.PLEX_CLIENTS:
            if item.find('Player').get('title') == client_name:
                for username in config.PLEX_AUTHORIZED_USERS:
                    if item.find('User').get('title') == username:
                        if item.find('Player').get('state') == 'paused' and CURRENT_STATUS != item.find('Player').get('state'):
                            CURRENT_STATUS = item.find('Player').get('state')
                            return True;


    return False


def is_plex_stopped(plex_status):
    global CURRENT_STATUS
    for item in plex_status.findall('Video'):
        for client_name in config.PLEX_CLIENTS:
            if item.find('Player').get('title') == client_name:
                for username in config.PLEX_AUTHORIZED_USERS:
                    if item.find('User').get('title') == username or CURRENT_STATUS == 'stopped':
                        return False;

    if CURRENT_STATUS == 'stopped':
        return False;

    CURRENT_STATUS = 'stopped'
    return True


def get_plex_status():
    global ACCESS_TOKEN, CURRENT_STATUS
    headers = {'X-Plex-Token': ACCESS_TOKEN, 'X-Plex-Client-Identifier': 'PlexWink'}
    r = requests.get('http://' + config.PLEX_HTTP_PATH + '/status/sessions', headers=headers)
    e = ElementTree.fromstring(r.text.encode('utf-8'))

    return e


def turn_off_lights():
    update_light_state(True, 0)
    sleep(2)
    update_light_state(False, 0)
    pass


def turn_on_lights():
    update_light_state(True, 1)
    pass


def dim_lights():
    update_light_state(True, 0)
    pass


def update_light_state(powered, brightness):
    headers = {'Authorization': 'Bearer ' + access_token}
    state_string = {'desired_state': {'brightness': brightness, 'powered': powered}};
    for group_id in get_wink_light_groups():
        requests.post("https://winkapi.quirky.com/groups/" + group_id + "/activate", json=state_string,headers=headers);


access_token = get_wink_token()
ACCESS_TOKEN = get_plex_token()

print('Listening for playing items')

while True:
    plex_status = get_plex_status()
    if is_plex_playing(plex_status):
        print 'Something is playing turning off lights'
        turn_off_lights()
    elif is_plex_paused(plex_status):
        print 'Something is paused dimming lights'
        dim_lights()
    elif is_plex_stopped(plex_status):
        print 'Nothing is playing turning on lights'
        turn_on_lights()

    sleep(2)
