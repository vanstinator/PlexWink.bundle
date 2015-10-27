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

import time
from time import sleep
import config
import websocket
from python import Plex, Wink
import logging
import json

logging.basicConfig()


CURRENT_STATUS = ''

plex = Plex.Plex()
wink = Wink.Wink()


def is_plex_playing(plex_status):
    global CURRENT_STATUS
    for item in plex_status.findall('Video'):
        for client_name in config.PLEX_CLIENTS:
            if item.find('Player').get('title') == client_name:
                for username in config.PLEX_AUTHORIZED_USERS:
                    if item.find('User').get('title') == username:
                        if item.find('Player').get('state') == 'playing' and CURRENT_STATUS != item.find('Player').get('state'):
                            CURRENT_STATUS = item.find('Player').get('state')
                            print(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (item.find('User').get('title'), CURRENT_STATUS, item.get('grandparentTitle'), item.get('title'), client_name))
                            turn_off_lights()
                            return False
                        elif item.find('Player').get('state') == 'paused' and CURRENT_STATUS != item.find('Player').get('state'):
                            CURRENT_STATUS = item.find('Player').get('state')
                            print(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (item.find('User').get('title'), CURRENT_STATUS, item.get('grandparentTitle'), item.get('title'), client_name))
                            dim_lights()
                            return False
                        else:
                            return False


    if CURRENT_STATUS == 'stopped':
        return False


    CURRENT_STATUS = 'stopped'
    print(time.strftime("%I:%M:%S") + " - Playback stopped");
    turn_on_lights()




def turn_off_lights():
    wink.update_light_state(True, 0)
    sleep(2)
    wink.update_light_state(False, 0)
    pass


def turn_on_lights():
    wink.update_light_state(True, 1)
    pass


def dim_lights():
    wink.update_light_state(True, 0)
    pass


def on_message(ws, message):
    json_object = json.loads(message)
    if json_object['type'] == 'playing':
        plex_status = plex.get_plex_status()

        # if json_object['_children'][0]['state'] == 'playing':
        is_plex_playing(plex_status)
        # turn_off_lights()

        # elif json_object['_children'][0]['state'] == 'paused':
        #     if is_plex_paused(plex_status):
        #         dim_lights()
        #
        # elif json_object['_children'][0]['state'] == 'stopped':
        #     if is_plex_stopped(plex_status):
        #         turn_on_lights()


if __name__ == "__main__":

    print('Listening for playing items')
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://127.0.0.1:32400/:/websockets/notifications?X-Plex-Token=" + plex.ACCESS_TOKEN,
                              on_message = on_message)
                              # on_error = on_error,
                              # on_close = on_close)

    # ws.on_open = on_open
    ws.run_forever()