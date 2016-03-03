import abc


# This is in the shared folder because Plex doesn't like attributes that start with "_". To enforce abstract functions
# I need to use abc, which requires __metaclass__ to be set.
class Automation(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        return

    @abc.abstractmethod
    def is_authenticated(self):
        """
        Function will return current connection state to the service provider

        :return: boolean
        """
        return

    @abc.abstractmethod
    def authenticate(self):
        """
        Function will authenticate with the service provder and return boolean successful

        :return: boolean
        """
        return

    @abc.abstractmethod
    def light_groups(self):
        """
        Function will return a list of dicts['name', 'id'] of all the light groups for the authenticated account.

        :return: list
        """
        return

    @abc.abstractmethod
    def change_group_state(self, **kwargs):
        """
        Function will change the state of the selected light group and return boolean successful.

        :param kwargs:
        :return: boolean
        """
        return
