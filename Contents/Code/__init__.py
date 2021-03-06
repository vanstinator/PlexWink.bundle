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
ICON = 'plexwink.png'
DELETE_ICON = 'plexwink-delete.png'
DISABLED_ICON = 'plexwink-disabled.png'
ENABLED_ICON = 'plexwink-enabled.png'
GROUPS_ICON = 'plexwink-groups.png'
DEVICE_ICON = 'plexwink-device.png'

####################################################################################################

THREAD_WEBSOCKET = "thread_websocket"
THREAD_CLIENTS = "thread_clients"
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
def MainMenu(header=NAME, message=""):
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)

    if message is not "":
        oc.message = message
        oc.header = header

    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(PREFIX, oc, CreateRoom, dktitle="Create a Room")
    else:
        oc.add(InputDirectoryObject(key=Callback(CreateRoom), title='Create a Room', prompt='Please enter a room name'))

    if Client.Product == 'Plex Web' and not ROOM_HANDLER.rooms:
        oc.add(DirectoryObject(key=Callback(MainMenu), title='You\'re using Plex Web. Please type a room name into the search field and hit enter to add your first room.'))

    for room_uuid, room in ROOM_HANDLER.rooms.iteritems():
        oc.add(DirectoryObject(key=Callback(EditRoom, room_uuid=room_uuid), title=room['name']))

    # This function is specific to Hue
    if is_hue_enabled():
        if not automation_services[hue.name].has_username():
            oc.add(DirectoryObject(key=Callback(ConnectHueBridge), title="Press button on Hue hub and then click here"))

    for name, service in automation_services.iteritems():
        if not service.is_authenticated():
            oc.add(DirectoryObject(key=Callback(MainMenu), title="Error connecting to " + service.name))
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


@route(PREFIX + '/ConnectHueBridge')
def ConnectHueBridge():
    automation_services[hue.name].authenticate()
    if automation_services[hue.name].is_authenticated():
        return MainMenu(message="Successfully connected to bridge")
    return MainMenu(message="Bridge Connection Failed")


@route(PREFIX + '/EditRoom')
def EditRoom(room_uuid, message=""):
    room = ROOM_HANDLER[room_uuid]
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)
    if message != "":
        oc.message = message
        # After every action with this as a callback we should assume something changed and therefore save the Data
        ROOM_HANDLER.save()
    oc.header = message

    oc.add(DirectoryObject(key=Callback(SetupLights, room_uuid=room_uuid), title='Select lights', thumb=R(GROUPS_ICON)))

    oc.add(DirectoryObject(key=Callback(SetupDevices, room_uuid=room_uuid), title='Select players', thumb=R(DEVICE_ICON)))

    if room['enabled']:
        oc.add(DirectoryObject(key=Callback(ToggleRoom, room_uuid=room_uuid), title='Disable this room', thumb=R(ENABLED_ICON)))
    else:
        oc.add(DirectoryObject(key=Callback(ToggleRoom, room_uuid=room_uuid), title='Enable this room', thumb=R(DISABLED_ICON)))

    oc.add(DirectoryObject(key=Callback(RemoveRoom, room_uuid=room_uuid), title='Delete Room', thumb=R(DELETE_ICON)))
    return oc


@route(PREFIX + '/SetupLights')
def SetupLights(room_uuid):
    oc = ObjectContainer(no_cache=True, no_history=True, replace_parent=True)

    for name, service in automation_services.iteritems():

        if not service.light_groups():
            oc.add(DirectoryObject(key=Callback(MainMenu), title="No groups found for " + service.name))
        for group in service.light_groups():

            if name not in ROOM_HANDLER[room_uuid]['lights']:
                ROOM_HANDLER[room_uuid]['lights'][name] = list()

            if group['id'] in ROOM_HANDLER[room_uuid]['lights'][name]:
                oc.add(DirectoryObject(key=Callback(RemoveLightGroup,
                                                    room_uuid=room_uuid,
                                                    group_id=group['id'],
                                                    service_name=name),
                                       title=group['name'] + " - " + name + " - Remove",
                                       thumb=R('hellohue.png')))
            else:
                oc.add(DirectoryObject(key=Callback(AddLightGroup,
                                                    room_uuid=room_uuid,
                                                    group_id=group['id'],
                                                    service_name=name),
                                       title=group['name'] + " - " + name + " - Add",
                                       thumb=R('hellohue.png')))
    return oc


@route(PREFIX + '/SetupDevices')
def SetupDevices(room_uuid):
    oc = ObjectContainer(no_cache=True,
                         no_history=True,
                         replace_parent=True)
    for device in plex.get_plex_devices():
        # XboxOne doesn't provide a player in the API. Need to manually display it
        # if 'player' in device.get('provides') or 'Xbox One' in device.get('platform'):
        if device.get('clientIdentifier') in ROOM_HANDLER[room_uuid]['devices']:
            oc.add(DirectoryObject(key=Callback(RemoveDeviceTrigger,
                                                room_uuid=room_uuid,
                                                client_identifier=device.get('clientIdentifier')),
                                   title="Remove " + device.get('name')))
        else:
            oc.add(DirectoryObject(key=Callback(AddDeviceTrigger,
                                                room_uuid=room_uuid,
                                                client_identifier=device.get('clientIdentifier')),
                                   title="Add " + device.get('name')))
    return oc


@route(PREFIX + '/ToggleRoom')
def ToggleRoom(room_uuid):
    if not ROOM_HANDLER[room_uuid]['enabled']:
        ROOM_HANDLER[room_uuid]['enabled'] = True
    else:
        ROOM_HANDLER[room_uuid]['enabled'] = False
        turn_on_lights(ROOM_HANDLER[room_uuid]['lights'])
        CURRENT_STATUS[room_uuid] = 'stopped'
    return EditRoom(room_uuid, message="Toggled Room: " + ROOM_HANDLER[room_uuid]['name'])


@route(PREFIX + '/RemoveRoom')
def RemoveRoom(room_uuid):
    del ROOM_HANDLER[room_uuid]
    return MainMenu()


@route(PREFIX + '/AddLightGroup')
def AddLightGroup(room_uuid, group_id, service_name):
    ROOM_HANDLER[room_uuid]['lights'][service_name].append(group_id)
    return EditRoom(room_uuid, message="Added light group: " + group_id)


@route(PREFIX + '/AddDeviceTrigger')
def AddDeviceTrigger(room_uuid, client_identifier):
    ROOM_HANDLER[room_uuid]['devices'].append(client_identifier)
    return EditRoom(room_uuid, message="Added device: " + client_identifier)


@route(PREFIX + '/RemoveLightGroup')
def RemoveLightGroup(room_uuid, group_id, service_name):
    ROOM_HANDLER[room_uuid]['lights'][service_name].remove(group_id)
    return EditRoom(room_uuid, message="Removed light group: " + group_id)


@route(PREFIX + '/RemoveDeviceTrigger')
def RemoveDeviceTrigger(room_uuid, client_identifier):
    ROOM_HANDLER[room_uuid]['devices'].remove(client_identifier)
    return EditRoom(room_uuid, message="Removed device: " + client_identifier)


####################################################################################################
# Called by the framework every time a user changes the prefs // Used to restart the Channel
####################################################################################################
@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
    Log('Validating Prefs')
    global plex, wink, hue, automation_services
    plex = Plex()

    automation_services = dict()

    wink = WinkAutomation(Prefs['WINK_CLIENT_ID'], Prefs['WINK_CLIENT_SECRET'], Prefs['WINK_USERNAME'], Prefs['WINK_PASSWORD'])
    hue = PhilipsHueAutomation(Prefs['HUE_IP_ADDRESS'])

    if is_wink_enabled():
        automation_services[wink.name] = wink
	
    if is_hue_enabled():
        automation_services[hue.name] = hue

    for name, service in automation_services.iteritems():
        Log(name + ' connection status is ' + str(service.is_authenticated()))


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


def is_hue_enabled():
    return Prefs['HUE_IP_ADDRESS'] != "HUE_IP_ADDRESS"


def is_wink_enabled():
    return Prefs['WINK_USERNAME'] != "WINK_USERNAME"\
           and Prefs['WINK_PASSWORD'] != "WINK_PASSWORD"\
           and Prefs['WINK_CLIENT_ID'] != "WINK_CLIENT_ID"\
           and Prefs['WINK_CLIENT_SECRET'] != "WINK_CLIENT_SECRET"


# TODO rewrite logic
def is_plex_playing(plex_status, room, room_uuid):
    global CURRENT_STATUS
    if not room['enabled']:
        return False
    if room_uuid not in CURRENT_STATUS:
        CURRENT_STATUS[room_uuid] = 'stopped'
    for video in plex_status.findall('Video'):
        # If we don't match on a recognized device let's just grab the next one.
        if video.find('Player').get('machineIdentifier') not in room['devices']:
            continue
        # We recognized a device. Anything at this point should just return. If a room has 2 devices they don't need to
        # step on each others toes. First one to start playing takes priority.
        if CURRENT_STATUS[room_uuid] == video.find('Player').get('state'):
            return
        if video.find('Player').get('state') == 'playing':
            CURRENT_STATUS[room_uuid] = video.find('Player').get('state')
            Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                video.find('User').get('title'), CURRENT_STATUS[room_uuid], video.get('grandparentTitle'),
                video.get('title'), video.find('Player').get('machineIdentifier')))
            turn_off_lights(room['lights'])
            # We got a match. Return the function
            return
        elif video.find('Player').get('state') == 'paused':
            CURRENT_STATUS[room_uuid] = video.find('Player').get('state')
            Log(time.strftime("%I:%M:%S") + " - %s %s %s - %s on %s." % (
                video.find('User').get('title'), CURRENT_STATUS[room_uuid], video.get('grandparentTitle'),
                video.get('title'), video.find('Player').get('machineIdentifier')))
            dim_lights(room['lights'])
            # We got a match. Return the function
            return
        # Play state hasn't changed and the file is still playing. Return and we'll check again next round.
        else:
            return

    if CURRENT_STATUS[room_uuid] == 'stopped':
        return False

    CURRENT_STATUS[room_uuid] = 'stopped'
    Log(time.strftime("%I:%M:%S") + " - Playback stopped")
    turn_on_lights(room['lights'])


def turn_off_lights(lights):
    for service, lights_list in lights.iteritems():
        # GE Link lights won't go dim before shutting off so it's jarring to turn them off and then have them come back
        # at full brightness for a half second before going dim.
        automation_services[service].change_group_state(lights_list, powered=True, dim=True)
        automation_services[service].change_group_state(lights_list, powered=False, dim=True)
    pass

def turn_on_lights(lights):
    for service, lights_list in lights.iteritems():
        automation_services[service].change_group_state(lights_list, powered=True, dim=False)
    pass

def dim_lights(lights):
    for service, lights_list in lights.iteritems():
        automation_services[service].change_group_state(lights_list, powered=True, dim=True)
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
                   'X-Plex-Version': '3.1.1',
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
        return XML.ElementFromURL(url="https://plex.tv/devices.xml?X-Plex-Token=" + PLEX_ACCESS_TOKEN,
                                  headers=HEADERS, cacheTime=360)
