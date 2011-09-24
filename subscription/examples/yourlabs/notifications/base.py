import datetime, time

import subscription

class BaseNotification(object):
    def emit(self, *args, **kwargs):
        backend = kwargs.pop('backend',None) or None

        if backend:
            backend_module = subscription.get_backends()[backend]()
            backend_module.emit(self, *args, **kwargs)

        for backend_module in subscription.get_backends().values():
            backend_module().emit(self, *args,**kwargs)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        if 'timestamp' in kwargs.keys():
            self.sent_at = datetime.datetime.fromtimestamp(kwargs['timestamp'])

    def __setattr__(self, key, value):
        if key == 'timestamp':
            self.__dict__['sent_at'] = datetime.datetime.fromtimestamp(value)
        elif key == 'sent_at':
            self.__dict__['timestamp'] = time.mktime(value.timetuple())
        
        self.__dict__[key] = value

    def to_dict(self, user):
        return {
            'timestamp': self.timestamp,
        }

    def get_display(self, user, backend):
        raise NotImplementedError()


