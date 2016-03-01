class Automation(object):

    def is_authenticated(self):
        """
        Function will return current connection state to the service provider

        :return: boolean
        """
        raise NotImplementedError("Must implement abstract method")

    def authenticate(self):
        """
        Function will authenticate with the service provder and return boolean successful

        :return: boolean
        """
        raise NotImplementedError("Must implement abstract method")

    def light_groups(self):
        """
        Function will return a list of dicts['name', 'id'] of all the light groups for the authenticated account.

        :return: list
        """
        raise NotImplementedError("Must implement abstract method")

    @property
    def group_state(self, **kwargs):
        """
        Function will return the state of the group

        :return:
        """
        raise NotImplementedError("Must implement abstract method")

    def change_group_state(self, **kwargs):
        """
        Function will change the state of the selected light group and return boolean successful.

        :param kwargs:
        :return: boolean
        """
        raise NotImplementedError("Must implement abstract method")