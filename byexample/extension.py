class Extension:
    def __init__(self, *, cfg, **unused):
        self.__cfg = cfg

    @property
    def cfg(self):
        ''' Property to access the configuration object.

            While not enforced, you must not modify this dictionary
            as any change will result in an undefined behavior.

            Consider it as read-only.
        '''
        return self.__cfg

    def _was_constructor_called(self):
        ''' Return if the constructor (__init__) was called or not '''
        try:
            _ = self.__cfg
            return True
        except AttributeError:
            return False
