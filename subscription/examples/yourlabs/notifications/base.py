import datetime, time

try:
   import cPickle as pickle
except:
   import pickle

import subscription

class BaseNotification(object):
    def emit(self, queues=None):
        local_queues = getattr(self, 'queues', None)
        if queues is None and local_queues:
            queues = self.queues

        if not queues:
            raise Exception('What queue should i emit to ?')

        for backend_module in subscription.get_backends().values():
            backend_module().emit(self, queues)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __setattr__(self, key, value):
        if key == 'timestamp':
            self.__dict__['sent_at'] = datetime.datetime.fromtimestamp(value)
        elif key == 'sent_at':
            self.__dict__['timestamp'] = time.mktime(value.timetuple())
        
        self.__dict__[key] = value

    def display(self, viewer=None, view=None):
        raise NotImplementedError()
