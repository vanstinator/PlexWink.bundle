# PlexWink
Control your Wink lights via Plex!

I picked up a Wink starter kit last week to automate the lights in my living/tv room with Plex. I'd like to share my script in case anyone else would find it useful.


**Behavior**
The script polls Plex every 2 seconds. If it detects an item is playing it behaves differently depending on the state.

* Playing - Dim the lights, and then shut them off
* Paused - Dim the lights
* Stopped - turn the lights on at full brightness
* Nothing detected - turn the lights on at full brightness


**Requirements**

* Python 2.7.X
* Requests - `pip install requests`
* Code - https://github.com/vanstinator/PlexWink

The config file is pretty simple. Fill out your plex login credentials, your wink credentials, and your wink API credentials. You can get the API keys by email support@winkapp.com and asking for a set.

`PLEX_CLIENT_TRIGGER_NAME` is the name of the client to monitor. Mine is just 'Living Room'

`WINK_ACTION_GROUP` is the Wink group name for your light bulbs. Mine is 'Entryway Hallway'

Both of those parameters are case and white-space sensitive, so match exactly what each respective application has.

**Roadmap**

* Allow for multiple Plex client names
* Specify which user it should activate for. Your brother in MN with a client named 'Living Room' shouldn't trigger your lights
* Allow multiple Wink groups. I technically have 2 right now at home, but one of them contains my room and hallway so Plex can hit both. A bit hacky really.
* Wink users should sympathize with this, but sometimes a bulb gets "stuck". So I'm planning to add some logic to check for that and force it to the correct state.
* Any other user requested things I don't think of.
