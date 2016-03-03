class Rooms(object):

    def __init__(self):
        self.rooms = dict()
        self.load()

    def load(self):
        if Data.Exists("rooms"):
            Log("Found existing saved rooms. Loading.")
            self.rooms = Data.LoadObject("rooms")
        else:
            Log("No existing rooms were found. Initializing empty list of rooms.")

    def save(self):
        Data.SaveObject("rooms", self.rooms)
        Log('saving object')

    def __getitem__(self, key):
        return self.rooms[key]

    def __setitem__(self, key, value):
        self.rooms[key] = value
        self.save()

    def __delitem__(self, key):
        del self.rooms[key]
        self.save()
