import base
from helpers import *

class TextNotification(base.BaseNotification):
    def __getstate__(self):
        if not getattr(self, 'lazy', False):
            self.rendered = self.display()
        else:
            if hasattr(self, 'rendered'):
                del self.rendered
        return super(TextNotification, self).__getstate__()

    def display(self, viewer=None, view=None):
        context = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Variable):
                value = value.value

            if viewer is not None and value == viewer:
                context[key] = u'you'
            elif hasattr(value, 'get_absolute_url'):
                context[key] = u'<a href="%s">%s</a>' % (
                    value.get_absolute_url(), unicode(value))
            else:
                context[key] = value
        return self.text % context
