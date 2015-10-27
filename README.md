# PlexWink
Control your Wink lights via Plex!

I picked up a Wink starter kit last week to automate the lights in my living/tv room with Plex. I'd like to share my script in case anyone else would find it useful.


**Behavior**
The script attaches to the Plex Notification web socket. If it receives a playing notification it checks if it's a video, the client name, and the user who owns the stream. If it matches your criteria it triggers these actions.

* Playing - Dim the lights, and then shut them off
* Paused - Dim the lights
* Stopped - turn the lights on at full brightness
* Nothing detected - turn the lights on at full brightness


**Requirements**
* Python 2.7.X
* Requests - `pip install requests`
* websocket-client - `pip install websocket-client`
* Code - https://github.com/vanstinator/PlexWink

The config file is pretty simple. Fill out your plex login credentials, your wink credentials, and your wink API credentials. You can get the API keys by email support@winkapp.com and asking for a set.

`PLEX_CLIENTs` is the list of names of the clients to monitor. Mine are ['Living Room', 'PlexMediaPlayer']

`WINK_ACTION_GROUPS` is the list of Wink group names for your light bulbs. Mine are ['Entryway Hallway', 'Living Room']

Both of those parameters are case and white-space sensitive, so match exactly what each respective application has.

**Roadmap**
* Wink users should sympathize with this, but sometimes a bulb gets "stuck". So I'm planning to add some logic to check for that and force it to the correct state.
* Any other user requested things I don't think of.
