
import collections

class AttrDictFields(collections.OrderedDict):
    '''OrderedDict subclass giving access to string keys via attribute access

    This class derives from collections.OrderedDict. Thus, the original
    order of the config entries in the input stream is maintained.
    '''

    def __getattr__(self, attr):
        # Take care that getattr() raises AttributeError, not KeyError.
        # Required e.g. for hasattr(), deepcopy and OrderedDict.
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise AttributeError("Attribute %r not found" % attr)
            
