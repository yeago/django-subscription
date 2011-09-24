import base

class TextNotification(base.BaseNotification):
    def __init__(self, **kwargs):
        super(TextNotification, self).__init__(**kwargs)

    def to_dict(self, user):
        data = super(TextNotification, self).to_dict(user)

        for key, value in self.format_kwargs.items():
            if user == value:
                self.format_kwargs['%s_display' % key] = u'you'
            elif hasattr(value, 'get_absolute_url'):
                self.format_kwargs['%s_display' % key] = u'<a href="%s">%s</a>' % (
                    value.get_absolute_url(), unicode(value))

        data['text'] = self.text.capitalize() % self.format_kwargs
        return data

    def get_display(self, user, backend):
        return self.text

class LazyTextNotification(TextNotification):
    def to_dict(self, user):
        data = super(TextNotification, self).to_dict(user)
        data['text'] = self.text
        data['format_kwargs'] = self.format_kwargs
        return  data

    def get_display(self, user, backend):
        return self.text % self.format_kwargs
