import time
from time import sleep
import requests
import websocket
import threading
import xml.etree.ElementTree as ElementTree
import logging
import json
import re
from DumbTools import DumbKeyboard

####################################################################################################

PREFIX = "/applications/PlexWink"
NAME = 'PlexWink'
ART = 'background.png'
ICON = 'hellohue.png'
PREFS_ICON = 'hellohue.png'
PROFILE_ICON = 'hellohue.png'

####################################################################################################

THREAD_WEBSOCKET = "thread_websocket";
THREAD_CLIENTS = "thread_clients";
DUMB_KEYBOARD_CLIENTS = ['Plex for iOS', 'Plex Media Player', 'Plex Home Theater', 'OpenPHT', 'Plex for Roku', 'iOS', 'Roku', 'tvOS' 'Konvergo']

CURRENT_STATUS = 'stopped'


####################################################################################################
# Start function
####################################################################################################
def Start():
    Log('Starting PlexWink .. Mwahahahaha!')
    HTTP.CacheTime = 0
    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ValidatePrefs()
    if not is_socket_thread_running():
        toggle_websocket_thread()


####################################################################################################
# Main menu
####################################################################################################
@handler(PREFIX, NAME, art=R(ART), thumb=R(ICON))
def MainMenu(header=NAME, message="Hello"):
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    if message is not "Hello":
        oc.header = header
        oc.message = message

    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(PREFIX, oc, CreateRoom,
                     dktitle="Test",
                     dkthumb=R('hellohue.png')
                     )
    else:
        oc.add(InputDirectoryObject(key=Callback(CreateRoom), title=("Create a Room"), prompt='Please enter a room name',
                                    thumb=R('hellohue.png')
                                    ))
    for key, value in rooms.iteritems():
        oc.add(PopupDirectoryObject(key=Callback(EditRoom, uuid=key), title=value['name'], thumb=R('hellohue.png')))
    if not is_socket_thread_running():
        oc.add(PopupDirectoryObject(key=Callback(ToggleState), title='Enable PlexWink', thumb=R('hellohue.png')))
    if is_socket_thread_running():
        oc.add(PopupDirectoryObject(key=Callback(ToggleState), title='Disable PlexWink', thumb=R('hellohue.png')))
        # oc.add(DirectoryObject(key=Callback(MyLights), title='My Lights', thumb=R(PREFS_ICON)))
        # if "thread_websocket" in str(threading.enumerate()):
        #     oc.add(DisableHelloHue())
        # if not "thread_websocket" in str(threading.enumerate()):
        #     oc.add(EnableHelloHue())
        # oc.add(DirectoryObject(key=Callback(AdvancedMenu), title='Advanced Menu', thumb=R(PREFS_ICON)))
        # Add item for setting preferences
        oc.add(PrefsObject(title=L('Preferences'), thumb=R(PREFS_ICON)))
    return oc

@route(PREFIX + '/CreateRoom')
def CreateRoom(query=""):
    room = dict()
    room['name'] = query
    rooms[String.UUID()] = room
    Data.SaveObject("rooms", rooms)
    return MainMenu(message="Creating a new Room named: " + query)


@route(PREFIX + '/EditRoom')
def EditRoom(uuid):
    room = rooms[uuid]
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    oc.header = room['name']
    if not 'lights' in room:
        lights = list()
        rooms[uuid]['lights'] = lights

    if not 'devices' in room:
        devices = list()
        rooms[uuid]['devices'] = devices

    Data.SaveObject("rooms", rooms)

    oc.add(PopupDirectoryObject(key=Callback(SetupLightGroup, uuid=uuid),
                                title='Select a lighting group for this room',
                                thumb=R('hellohue.png')))

    oc.add(PopupDirectoryObject(key=Callback(SetupDevices, uuid=uuid),
                                title='Pick device triggers',
                                thumb=R('hellohue.png')))

    oc.add(PopupDirectoryObject(key=Callback(RemoveRoom, uuid=uuid),
                                title='Delete Room',
                                thumb=R('hellohue.png')))
    return oc

@route(PREFIX + '/SetupLightGroup')
def SetupLightGroup(uuid):
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    oc.message = "Please select the following "
    rooms = Data.LoadObject("rooms")
    for group in wink.get_wink_groups():
        # Wink sometimes has empty groups returned by the API. This will check for hub ownership for each group
        # and only display those with a hub attached.
        if group['members']:
            if group['group_id'] in rooms[uuid]['lights']:
                oc.add(PopupDirectoryObject(key=Callback(RemoveLightGroup,
                                            uuid=uuid,
                                            group_id=group['group_id']),
                                            title="Remove " + group['name'],
                                            thumb=R('hellohue.png')))
            else:
                oc.add(PopupDirectoryObject(key=Callback(AddLightGroup,
                                            uuid=uuid,
                                            group_id=group['group_id']),
                                            title="Add " + group['name'],
                                            thumb=R('hellohue.png')))
    return oc

@route(PREFIX + '/SetupDevices')
def SetupDevices(uuid):
    rooms = Data.LoadObject("rooms")
    oc = ObjectContainer(no_cache=True,
                         no_history=True,
                         replace_parent=True)
    for device in plex.get_plex_devices():
        # if "player" in device.get('provides'):
        if device.get('clientIdentifier') in rooms[uuid]['devices']:
            oc.add(PopupDirectoryObject(key=Callback(RemoveDeviceTrigger,
                                        uuid=uuid,
                                        client_identifier=device.get('clientIdentifier')),
                                        title="Remove " + device.get('name')))
        else:
            oc.add(PopupDirectoryObject(key=Callback(AddDeviceTrigger,
                                        uuid=uuid,
                                        client_identifier=device.get('clientIdentifier')),
                                        title="Add " + device.get('name')))
    oc.message = "Please select the following "
    return oc

@route(PREFIX + '/RemoveRoom')
def RemoveRoom(uuid):
    del rooms[uuid]
    Data.SaveObject("rooms", rooms)
    return MainMenu()

def AddLightGroup(uuid, group_id):
    rooms[uuid]['lights'].append(group_id)
    Data.SaveObject("rooms", rooms)
    return SetupLightGroup(uuid)

def AddDeviceTrigger(uuid, client_identifier):
    rooms[uuid]['devices'].append(client_identifier)
    Data.SaveObject("rooms", rooms)
    return SetupDevices(uuid)

def RemoveDeviceTrigger(uuid, client_identifier):
    rooms[uuid]['devices'].remove(client_identifier)
    Data.SaveObject("rooms", rooms)
    return SetupDevices(uuid)

def RemoveLightGroup(uuid, group_id):
    rooms[uuid]['lights'].remove(group_id)
    Data.SaveObject("rooms", rooms)
    return SetupLightGroup(uuid)

def TestPrompt(query=""):
    return MainMenu(header=NAME, message=query)


def ToggleState():
    toggle_websocket_thread()
    return MainMenu()


####################################################################################################
# Called by the framework every time a user changes the prefs // Used to restart the Channel
####################################################################################################
@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
    Log('Validating Prefs')
    global plex, wink, rooms

    if Data.Exists("rooms"):
        Log("Found existing saved rooms. Loading.")
        rooms = Data.LoadObject("rooms")
        Log(rooms)
    else:
        Log("No existing rooms were found. Initializing empty list of rooms.")
        rooms = dict()
    plex = Plex()
    wink = Wink()


def run_websocket_watcher():
    global ws
    Log('Thread is starting websocket listener')
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "ws://127.0.0.1:" + Prefs['PLEX_PORT'] + "/:/websockets/notifications?X-Plex-Token=" + PLEX_ACCESS_TOKEN,
        on_message=on_message)
    Log("Up and running, listening")
    ws.run_forever()


def is_socket_thread_running():
    if THREAD_WEBSOCKET in str(threading.enumerate()):
        return True
    if not THREAD_WEBSOCKET in str(threading.enumerate()):
        return False


def toggle_websocket_thread():
    if is_socket_thread_running():
        Log('Closing websocket thread')
        turn_on_lights()
        ws.close()
    else:
        Log('Opening websocket thread')
        threading.Thread(target=run_websocket_watcher, name=THREAD_WEBSOCKET).start()


def is_plex_playing(plex_status):
    global CURRENT_STATUS
    for key, value in rooms.iteritems():
        room = value
        for item in plex_status.findall('Video'):
            for client_identifier in room['devices']:
                if item.find('Player').get('machineIdentifier') == client_identifier:
                    if item.find('Player').get('state') == 'playing' and CURRENT_STATUS != item.find('Player').get(
                            'state'):
                        CURRENT_STATUS = item.find('Player').get('state')
                        Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                        item.find('User').get('title'), CURRENT_STATUS, item.get('grandparentTitle'),
                        item.get('title'), client_identifier))
                        Log('should turn off')
                        turn_off_lights(room['lights'])
                        return False
                    elif item.find('Player').get('state') == 'paused' and CURRENT_STATUS != item.find('Player').get(
                            'state'):
                        CURRENT_STATUS = item.find('Player').get('state')
                        Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                        item.find('User').get('title'), CURRENT_STATUS, item.get('grandparentTitle'),
                        item.get('title'), client_identifier))
                        dim_lights(room['lights'])
                        return False
                    else:
                        return False

    if CURRENT_STATUS == 'stopped':
        return False

    CURRENT_STATUS = 'stopped'
    Log(time.strftime("%I:%M:%S") + " - Playback stopped")
    turn_on_lights(room['lights'])


def turn_off_lights(lights):
    wink.update_light_state(True, 0, lights)
    sleep(2)
    wink.update_light_state(False, 0, lights)
    pass


def turn_on_lights(lights):
    wink.update_light_state(True, 1, lights)
    pass


def dim_lights(lights):
    wink.update_light_state(True, 0, lights)
    pass


def on_message(ws, message):
    json_object = json.loads(message)
    if json_object['type'] == 'playing':
        plex_status = plex.get_plex_status()
        is_plex_playing(plex_status)


class Plex:
    def __init__(self):
        global PLEX_ACCESS_TOKEN

        HEADERS = {'X-Plex-Product': 'Automating Home Lighting',
                   'X-Plex-Version': '2.0.0',
                   'X-Plex-Client-Identifier': 'PlexWink',
                   'X-Plex-Device': 'PC',
                   'X-Plex-Device-Name': 'PlexWink'}

        Log("Initializing Plex class")
        Log("-Getting Token")
        global PLEX_ACCESS_TOKEN, HEADERS
        PLEX_ACCESS_TOKEN = self.get_plex_token()

    """
    :returns A Plex Token
    """

    def get_plex_token(self):
        auth = {'user[login]': Prefs['PLEX_USERNAME'], 'user[password]': Prefs['PLEX_PASSWORD']}

        r = requests.post('https://plex.tv/users/sign_in.json', params=auth, headers=HEADERS)

        data = json.loads(r.text)

        return data['user']['authentication_token']

    """
    :returns Current Plex Status Object
    """

    def get_plex_status(self):
        r = requests.get(
            'http://127.0.0.1:' + Prefs['PLEX_PORT'] + '/status/sessions?X-Plex-Token=' + PLEX_ACCESS_TOKEN,
            headers=HEADERS)
        e = ElementTree.fromstring(r.text.encode('utf-8'))
        return e

    def get_plex_devices(self):
        Log('Requesting devices from Plex')
        return XML.ElementFromURL(url="https://www.plex.tv/devices.xml?X-Plex-Token=" + PLEX_ACCESS_TOKEN, headers=HEADERS, cacheTime=360)


class Wink:
    def __init__(self):
        global pattern
        Log("Initializing Wink class")
        Log("-Getting Token")
        pattern = re.compile("^\s+|\s*,\s*|\s+$")
        global WINK_ACCESS_TOKEN, LIGHT_GROUPS
        WINK_ACCESS_TOKEN = self.get_wink_token()
        LIGHT_GROUPS = self.get_wink_light_group_ids()

    def get_wink_token(self):
        auth_string = {'client_id': Prefs['WINK_CLIENT_ID'],
                       'client_secret': Prefs['WINK_CLIENT_SECRET'],
                       'username': Prefs['WINK_USERNAME'],
                       'password': Prefs['WINK_PASSWORD'],
                       'grant_type': 'password'}

        r = requests.post("https://winkapi.quirky.com/oauth2/token/", json=auth_string)

        data = json.loads(r.text)

        return data['access_token']

    def get_wink_light_group_ids(self):
        array = []
        headers = {'Authorization': 'Bearer ' + WINK_ACCESS_TOKEN}
        r = requests.get("https://winkapi.quirky.com/users/me/groups", headers=headers)
        json_object = json.loads(r.text)

        for group in json_object['data']:
            for local_group in pattern.split(Prefs['WINK_ACTION_GROUPS']):
                if group['name'] == local_group:
                    array.append(group['group_id'])

        return array

    def get_wink_groups(self):
        array = []
        headers = {'Authorization': 'Bearer ' + WINK_ACCESS_TOKEN}
        r = requests.get("https://winkapi.quirky.com/users/me/groups", headers=headers)
        json_object = json.loads(r.text)
        # for group in json_object['data']:
        #     for local_group in pattern.split(Prefs['WINK_ACTION_GROUPS']):
        #         if group['name'] == local_group:
        #             array.append(group['group_id'])

        return json_object['data']

    def update_light_state(self, powered, brightness, lights):
        headers = {'Authorization': 'Bearer ' + WINK_ACCESS_TOKEN}
        state_string = {'desired_state': {'brightness': brightness, 'powered': powered}}
        for group_id in lights:
            Log(time.strftime(
                "%I:%M:%S") + " - changing light group %s powered state to %s and brightness state to %s" % (group_id,
                                                                                                             "ON" if powered else "OFF",
                                                                                                             "DIM" if brightness == 0 else "FULL"))
            requests.post("https://winkapi.quirky.com/groups/" + group_id + "/activate", json=state_string,
                          headers=headers)
