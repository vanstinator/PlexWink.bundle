import time
from time import sleep
import requests
import websocket
import threading
import xml.etree.ElementTree as ElementTree
import json
import re
from WinkAutomation import WinkAutomation
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

CURRENT_STATUS = dict()


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
        toggle_socket_thread()


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
        DumbKeyboard(PREFIX, oc, CreateRoom, dktitle="Create a Room")
    else:
        oc.add(InputDirectoryObject(key=Callback(CreateRoom), title=("Create a Room"), prompt='Please enter a room name'))
    for key, value in rooms.iteritems():
        oc.add(DirectoryObject(key=Callback(EditRoom, uuid=key), title=value['name'], thumb=R('hellohue.png')))
    if not is_socket_thread_running():
        oc.add(DirectoryObject(key=Callback(ToggleState), title='Enable PlexWink', thumb=R('hellohue.png')))
    if is_socket_thread_running():
        oc.add(DirectoryObject(key=Callback(ToggleState), title='Disable PlexWink', thumb=R('hellohue.png')))
        # oc.add(PrefsObject(title=L('Preferences'), thumb=R(PREFS_ICON))) TODO add new auth check
    return oc

@route(PREFIX + '/CreateRoom')
def CreateRoom(query=""):
    room = dict()
    room['name'] = query
    rooms[String.UUID()] = room
    Data.SaveObject("rooms", rooms)
    return MainMenu(message="Creating a new Room named: " + query)


@route(PREFIX + '/EditRoom')
def EditRoom(uuid, message=""):
    room = rooms[uuid]
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    if message != "":
        oc.message = ""
    oc.header = message
    if not 'lights' in room:
        lights = list()
        rooms[uuid]['lights'] = lights

    if not 'devices' in room:
        devices = list()
        rooms[uuid]['devices'] = devices

    Data.SaveObject("rooms", rooms)

    oc.add(DirectoryObject(key=Callback(SetupLights, uuid=uuid),
                           title='Select lights'))

    oc.add(DirectoryObject(key=Callback(SetupDevices, uuid=uuid),
                           title='Select players'))

    oc.add(DirectoryObject(key=Callback(RemoveRoom, uuid=uuid),
                           title='Delete Room'))
    return oc


@route(PREFIX + '/SetupLights')
def SetupLights(uuid):
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    oc.message = "Please select the following "
    rooms = Data.LoadObject("rooms")
    for group in wink.light_groups():
        # Wink sometimes has empty groups returned by the API. This will check for hub ownership for each group
        # and only display those with a hub attached.
        if group['members']:
            if group['group_id'] in rooms[uuid]['lights']:
                oc.add(DirectoryObject(key=Callback(RemoveLightGroup,
                                            uuid=uuid,
                                            group_id=group['group_id']),
                                            title="Remove " + group['name'],
                                            thumb=R('hellohue.png')))
            else:
                oc.add(DirectoryObject(key=Callback(AddLightGroup,
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
            oc.add(DirectoryObject(key=Callback(RemoveDeviceTrigger,
                                        uuid=uuid,
                                        client_identifier=device.get('clientIdentifier')),
                                        title="Remove " + device.get('name')))
        else:
            oc.add(DirectoryObject(key=Callback(AddDeviceTrigger,
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


@route(PREFIX + '/AddLightGroup')
def AddLightGroup(uuid, group_id):
    rooms[uuid]['lights'].append(group_id)
    Data.SaveObject("rooms", rooms)
    return EditRoom(uuid, message="Added light group: " + group_id)


@route(PREFIX + '/AddDeviceTrigger')
def AddDeviceTrigger(uuid, client_identifier):
    rooms[uuid]['devices'].append(client_identifier)
    Data.SaveObject("rooms", rooms)
    return EditRoom(uuid, message="Added device: " + client_identifier)


@route(PREFIX + '/RemoveDeviceTrigger')
def RemoveDeviceTrigger(uuid, client_identifier):
    rooms[uuid]['devices'].remove(client_identifier)
    Data.SaveObject("rooms", rooms)
    return EditRoom(uuid, message="Removed device: " + client_identifier)


@route(PREFIX + '/RemoveLightGroup')
def RemoveLightGroup(uuid, group_id):
    rooms[uuid]['lights'].remove(group_id)
    Data.SaveObject("rooms", rooms)
    return EditRoom(uuid, message="Removed light group: " + group_id)


def ToggleState():
    toggle_socket_thread()
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
    wink = WinkAutomation(Prefs['WINK_CLIENT_ID'], Prefs['WINK_CLIENT_SECRET'], Prefs['WINK_USERNAME'], Prefs['WINK_PASSWORD'])
    wink.authenticate()
    Log('Wink connection status is ' + str(wink.is_authenticated()))


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


def toggle_socket_thread():
    if is_socket_thread_running():
        Log('Closing websocket thread')
        turn_on_lights()
        ws.close()
    else:
        Log('Opening websocket thread')
        threading.Thread(target=run_websocket_watcher, name=THREAD_WEBSOCKET).start()


def is_plex_playing(plex_status, room, uuid):
    global CURRENT_STATUS
    if uuid not in CURRENT_STATUS:
        CURRENT_STATUS[uuid] = 'stopped'
    for item in plex_status.findall('Video'):
        for client_identifier in room['devices']:
            if item.find('Player').get('machineIdentifier') == client_identifier:
                if item.find('Player').get('state') == 'playing' and CURRENT_STATUS[uuid] != item.find('Player').get(
                        'state'):
                    CURRENT_STATUS[uuid] = item.find('Player').get('state')
                    Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                    item.find('User').get('title'), CURRENT_STATUS[uuid], item.get('grandparentTitle'),
                    item.get('title'), client_identifier))
                    Log('should turn off')
                    turn_off_lights(room['lights'])
                    return False
                elif item.find('Player').get('state') == 'paused' and CURRENT_STATUS[uuid] != item.find('Player').get(
                        'state'):
                    CURRENT_STATUS[uuid] = item.find('Player').get('state')
                    Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                    item.find('User').get('title'), CURRENT_STATUS[uuid], item.get('grandparentTitle'),
                    item.get('title'), client_identifier))
                    dim_lights(room['lights'])
                    return False
                else:
                    return False

    if CURRENT_STATUS[uuid] == 'stopped':
        return False

    CURRENT_STATUS[uuid] = 'stopped'
    Log(time.strftime("%I:%M:%S") + " - Playback stopped")
    turn_on_lights(room['lights'])


def turn_off_lights(lights):
    wink.change_group_state(True, 0, lights)
    sleep(2)
    wink.change_group_state(False, 0, lights)
    pass


def turn_on_lights(lights):
    wink.change_group_state(True, 1, lights)
    pass


def dim_lights(lights):
    wink.change_group_state(True, 0, lights)
    pass


def on_message(ws, message):
    json_object = json.loads(message)
    if json_object['type'] == 'playing':
        plex_status = plex.get_plex_status()
        for key, value in rooms.iteritems():
            is_plex_playing(plex_status, value, key)

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
