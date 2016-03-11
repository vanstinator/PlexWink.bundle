# Plex Wink

## This is a development branch that will contain early support for Philips Hue as well as v2 of the Wink api. Features will be unstable until moved to master. Please take this into consideration when installing this branch

PlexWink is a Plex Channel that is designed to give Plex control of your home's smart lighting capabilities. The channel will monitor your Plex server for play criteria that you set up with the channel. If any of the criteria are met PlexWink will turn your lights off when Plex is playing a media item and will turn them back on when you are finished.

The channel logic is designed around the concept of a room. A room is just a collection of lights and clients. If you have multiple rooms in your home where you use Plex the channel supports that too! PlexWink can create and store as many rooms as one needs.

### Creating a Room

To create a room in PlexWink click `Create a Room` and fill in the text field with the desired room name.

> Plex Web will not show this button. Instead text must be entered in the search field. From the home screen of PlexWink type in the name of the room being created into the search field and hit enter.

PlexWink will take you back to the home screen of the channel where there will now be a button with the name of the new room you just created.

### Adding lights and devices

Navigate to the home screen of PlexWink and click on the room that is to be configured. On the next screen click on `Select lights`. A list of the Wink light groups will be displayed. Select the groups you would like to trigger for this room. After selecting the lights click `Select devices` and select the devices that are in the room. These devices will determine whether or not Plex controls your lights when media playback is detected.

### Support

Support is available on the Plex forums. Please do not open an issue on GitHub unless told by me or you have done sufficient technical analysis. I will close any issues that are not technical in nature. The forum thread where support can be had is https://forums.plex.tv/discussion/205647/rel-plexwink-control-your-wink-smart-lights-with-plex

**Requirements**
* A current version of PMS
* A Wink Smart Hub and some smart light bulbs
* At least one group configured in Wink

The config is pretty simple. Fill out your plex login credentials, your wink credentials, and your wink API credentials. You can get the API keys by emailing support@winkapp.com. You need v1 API keys. PlexWink will not work with API v2.

**Roadmap**
* Fix bugs
* Add imagery