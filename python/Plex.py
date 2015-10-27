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
import xml.etree.ElementTree as ElementTree


class Plex:

    ACCESS_TOKEN = '';

    HEADERS = {'X-Plex-Product': 'Automating Home Lighting',
                   'X-Plex-Version': '1.2.0',
                   'X-Plex-Client-Identifier': 'PlexWink',
                   'X-Plex-Device': 'PC',
                   'X-Plex-Device-Name': 'PlexWink'}

    def __init__(self):
        print("Initializing Plex class")
        print("-Getting Token")
        global ACCESS_TOKEN, HEADERS
        ACCESS_TOKEN = self.get_plex_token()

    """
    :return A Plex Token
    """
    def get_plex_token(self):
        auth = {'user[login]': config.PLEX_USERNAME, 'user[password]': config.PLEX_PASSWORD}

        r = requests.post('https://plex.tv/users/sign_in.json', params=auth, headers=self.HEADERS)

        data = json.loads(r.text)

        return data['user']['authentication_token']

    """
    :returns Current Plex Status Object
    """
    def get_plex_status(self):
        r = requests.get('http://' + config.PLEX_HTTP_PATH + '/status/sessions?X-Plex-Token=' + ACCESS_TOKEN, headers=self.HEADERS)
        e = ElementTree.fromstring(r.text.encode('utf-8'))
        return e

