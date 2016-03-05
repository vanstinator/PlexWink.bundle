import json
import threading
import time
import xml.etree.ElementTree as ElementTree

import requests
import websocket

from WinkAutomation import WinkAutomation
from PhilipsHueAutomation import PhilipsHueAutomation
from DumbTools import DumbKeyboard
from RoomsHandler import Rooms

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
DUMB_KEYBOARD_CLIENTS = ['Plex for iOS', 'Plex Media Player', 'Plex Home Theater', 'OpenPHT', 'Plex for Roku', 'iOS',
                         'Roku', 'tvOS' 'Konvergo']

CURRENT_STATUS = dict()
ROOM_HANDLER = Rooms()


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
        oc.add(
            InputDirectoryObject(key=Callback(CreateRoom), title=("Create a Room"), prompt='Please enter a room name'))
    for key, value in ROOM_HANDLER.rooms.iteritems():
        oc.add(DirectoryObject(key=Callback(EditRoom, uuid=key), title=value['name'], thumb=R('hellohue.png')))
    return oc


@route(PREFIX + '/CreateRoom')
def CreateRoom(query=""):
    room = dict()
    room['name'] = query
    room['lights'] = dict()
    room['devices'] = list()
    room['enabled'] = True
    ROOM_HANDLER[String.UUID()] = room
    return MainMenu(message="Creating a new Room named: " + query)


@route(PREFIX + '/EditRoom')
def EditRoom(uuid, message=""):
    room = ROOM_HANDLER[uuid]
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    if message != "":
        oc.message = message
        # After every action with this as a callback we should assume something changed and therefore save to Data
        ROOM_HANDLER.save()
    oc.header = message

    oc.add(DirectoryObject(key=Callback(SetupLights, uuid=uuid),
                           title='Select lights'))

    oc.add(DirectoryObject(key=Callback(SetupDevices, uuid=uuid),
                           title='Select players'))

    if room['enabled']:
        oc.add(DirectoryObject(key=Callback(ToggleRoom, uuid=uuid),
                               title='Disable this room'))
    else:
        oc.add(DirectoryObject(key=Callback(ToggleRoom, uuid=uuid),
                               title='Enable this room'))

    oc.add(DirectoryObject(key=Callback(RemoveRoom, uuid=uuid),
                           title='Delete Room'))
    return oc


@route(PREFIX + '/SetupLights')
def SetupLights(uuid):
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    oc.message = "Please select the following "
    for name, service in automation_services.iteritems():
        Log('Adding items for ' + name)
        for group in service.light_groups():
            if name not in ROOM_HANDLER[uuid]['lights']:
                ROOM_HANDLER[uuid]['lights'][name] = list()
            if group['id'] in ROOM_HANDLER[uuid]['lights'][name]:
                oc.add(DirectoryObject(key=Callback(RemoveLightGroup,
                                                    uuid=uuid,
                                                    group_id=group['id']),
                                       title=name + " - Remove " + group['name'],
                                       thumb=R('hellohue.png')))
            else:
                oc.add(DirectoryObject(key=Callback(AddLightGroup,
                                                    uuid=uuid,
                                                    group_id=group['id'],
                                                    service_name=name),
                                       title=name + " - Add " + group['name'],
                                       thumb=R('hellohue.png')))
    return oc


@route(PREFIX + '/SetupDevices')
def SetupDevices(uuid):
    oc = ObjectContainer(no_cache=True,
                         no_history=True,
                         replace_parent=True)
    for device in plex.get_plex_devices():
        # if "player" in device.get('provides'):
        if device.get('clientIdentifier') in ROOM_HANDLER[uuid]['devices']:
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


@route(PREFIX + '/ToggleRoom')
def ToggleRoom(uuid):
    if not ROOM_HANDLER[uuid]['enabled']:
        ROOM_HANDLER[uuid]['enabled'] = True
    else:
        ROOM_HANDLER[uuid]['enabled'] = False
        turn_on_lights(ROOM_HANDLER[uuid]['lights'])
        CURRENT_STATUS[uuid] = 'stopped'
    return EditRoom(uuid, message="Toggled Room: " + ROOM_HANDLER[uuid]['name'])


@route(PREFIX + '/RemoveRoom')
def RemoveRoom(uuid):
    del ROOM_HANDLER[uuid]
    return MainMenu()


@route(PREFIX + '/AddLightGroup')
def AddLightGroup(uuid, group_id, service_name):
    ROOM_HANDLER[uuid]['lights'][service_name].append(group_id)
    return EditRoom(uuid, message="Added light group: " + group_id)


@route(PREFIX + '/AddDeviceTrigger')
def AddDeviceTrigger(uuid, client_identifier):
    ROOM_HANDLER[uuid]['devices'].append(client_identifier)
    return EditRoom(uuid, message="Added device: " + client_identifier)


@route(PREFIX + '/RemoveLightGroup')
def RemoveLightGroup(uuid, group_id):
    ROOM_HANDLER[uuid]['lights'].remove(group_id)
    return EditRoom(uuid, message="Removed light group: " + group_id)


@route(PREFIX + '/RemoveDeviceTrigger')
def RemoveDeviceTrigger(uuid, client_identifier):
    ROOM_HANDLER[uuid]['devices'].remove(client_identifier)
    return EditRoom(uuid, message="Removed device: " + client_identifier)


####################################################################################################
# Called by the framework every time a user changes the prefs // Used to restart the Channel
####################################################################################################
@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
    Log('Validating Prefs')
    global plex, wink, automation_services

    automation_services = dict()
    plex = Plex()
    wink = WinkAutomation(Prefs['WINK_CLIENT_ID'], Prefs['WINK_CLIENT_SECRET'], Prefs['WINK_USERNAME'], Prefs['WINK_PASSWORD'])
    hue = PhilipsHueAutomation(Prefs['HUE_IP_ADDRESS'], None)
    automation_services[wink.name] = wink
    automation_services[hue.name] = hue
    Log(automation_services)
    Log('Wink connection status is ' + str(wink.is_authenticated()))
    Log('Hue connection status is ' + str(hue.is_authenticated()))


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
    if THREAD_WEBSOCKET not in str(threading.enumerate()):
        return False


def toggle_socket_thread():
    if is_socket_thread_running():
        Log('Closing websocket thread')
        ws.close()
    else:
        Log('Opening websocket thread')
        threading.Thread(target=run_websocket_watcher, name=THREAD_WEBSOCKET).start()


# TODO rewrite logic
def is_plex_playing(plex_status, room, uuid):
    global CURRENT_STATUS
    if not room['enabled']:
        return False
    if uuid not in CURRENT_STATUS:
        CURRENT_STATUS[uuid] = 'stopped'
    for video in plex_status.findall('Video'):
        # If we don't match on a recognized device let's just grab the next one.
        if video.find('Player').get('machineIdentifier') not in room['devices']:
            continue
        # We recognized a device. Anything at this point should just return. If a room has 2 devices they don't need to
        # step on each others toes. First one to start playing takes priority.
        if CURRENT_STATUS[uuid] == video.find('Player').get('state'):
            return
        if video.find('Player').get('state') == 'playing':
            CURRENT_STATUS[uuid] = video.find('Player').get('state')
            Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                video.find('User').get('title'), CURRENT_STATUS[uuid], video.get('grandparentTitle'),
                video.get('title'), video.find('Player').get('machineIdentifier')))
            turn_off_lights(room['lights'])
            # We got a match. Return the function
            return
        elif video.find('Player').get('state') == 'paused':
            CURRENT_STATUS[uuid] = video.find('Player').get('state')
            Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                video.find('User').get('title'), CURRENT_STATUS[uuid], video.get('grandparentTitle'),
                video.get('title'), video.find('Player').get('machineIdentifier')))
            dim_lights(room['lights'])
            # We got a match. Return the function
            return
        # Play state hasn't changed and the file is still playing. Return and we'll check again next round.
        else:
            return

    if CURRENT_STATUS[uuid] == 'stopped':
        return False

    CURRENT_STATUS[uuid] = 'stopped'
    Log(time.strftime("%I:%M:%S") + " - Playback stopped")
    turn_on_lights(room['lights'])


def turn_off_lights(lights):
    for service, lights_list in lights.iteritems():
        # GE Link lights won't go dim before shutting off so it's jarring to turn them off and then have them come back
        # at full brightness for a half second before going dim.
        automation_services[service].change_group_state(True, 0, lights_list)
        automation_services[service].change_group_state(False, 0, lights_list)
    pass

def turn_on_lights(lights):
    for service, lights_list in lights.iteritems():
        automation_services[service].change_group_state(True, 1, lights_list)
    pass

def dim_lights(lights):
    for service, lights_list in lights.iteritems():
        automation_services[service].change_group_state(True, 0, lights_list)
    pass

def on_message(ws, message):
    json_object = json.loads(message)
    if json_object['type'] == 'playing':
        plex_status = plex.get_plex_status()
        for key, value in ROOM_HANDLER.rooms.iteritems():
            is_plex_playing(plex_status, value, key)


class Plex:
    def __init__(self):
        global PLEX_ACCESS_TOKEN

        HEADERS = {'X-Plex-Product': 'Automating Home Lighting',
                   'X-Plex-Version': '3.1.0',
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
        return XML.ElementFromURL(url="https://www.plex.tv/devices.xml?X-Plex-Token=" + PLEX_ACCESS_TOKEN,
                                  headers=HEADERS, cacheTime=360)
