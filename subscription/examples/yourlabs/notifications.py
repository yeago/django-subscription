import datetime

class BaseNotification(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        if 'timestamp' in kwargs.keys():
            self.sent_at = datetime.datetime.fromtimestamp(kwargs['timestamp'])

    def __setattr__(self, key, value):
        if key == 'timestamp':
            self.sent_at = datetime.datetime.fromtimestamp(kwargs['timestamp'])
        elif key == 'sent_at':
            self.timestamp = time.mktime(datetime.datetime.now().timetuple())

        return super(BaseNotification, self).__setattr__(key, value)

    def to_dict(self, user):
        return {
            'timestamp': self.timestamp,
        }

    def get_display(self, user, backend):
        raise NotImplementedError()

class TextNotification(BaseNotification):
    def to_dict(self, user):
        data = super(TextNotification, self).to_dict(user, sent_at)
        data['text'] = self.text % self.format_kwargs
        return data

    def get_display(self, user, backend):
        return self.text

class LazyTextNotification(TextNotification):
    def to_dict(self, user):
        data = super(TextNotification, self).to_dict(user, sent_at)
        data['text'] = self.text
        data['format_kwargs'] = self.format_kwargs
        return  data

    def get_display(self, user, backend):
        return self.text % self.format_kwargs
