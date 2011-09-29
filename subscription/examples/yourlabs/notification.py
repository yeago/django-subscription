import datetime, time

try:
   import cPickle as pickle
except:
   import pickle

from django import template
from django.core.cache import cache
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType

import subscription

class Notification(object):
    def emit(self, queues=None):
        local_queues = getattr(self, 'queues', None)
        if queues is None and local_queues:
            queues = self.queues

        if queues:
            for backend_module in subscription.get_backends().values():
                backend_module().emit(self, queues)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __setattr__(self, key, value):
        actual_value = getattr(value, 'value', value)

        if key == 'timestamp':
            self.__dict__['sent_at'] = datetime.datetime.fromtimestamp(
                actual_value)
        elif key == 'sent_at':
            self.__dict__['timestamp'] = time.mktime(actual_value.timetuple())
        
        self.__dict__[key] = value

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)

        if isinstance(value, Variable):
            return value.value

        return value

    def __getattr__(self, name):
        if '_variable' in name:
            name = name.split('_')[:-1]
            return object.__getattribute__(self, name)
        else:
            raise AttributeError

    def __getstate__(self):
        if getattr(self, 'lazy', False):
            if hasattr(self, 'rendered'):
                del self.rendered
        else:
            self.rendered = self.display()

        if not getattr(self, 'sent_at', False):
            self.sent_at = datetime.datetime.now()

        return self.__dict__

    @property
    def context(self):
        if not hasattr(self, '_context'):
            self._context = self.get_context()
        return self._context

    def get_context(self):
        context = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Variable):
                value = value.value
            context[key] = value
        return context

    def render_text(self, viewer=None, view=None):
        context = self.get_context()

        for key, value in context.items():
            if viewer is not None and value == viewer:
                context[key] = u'you'
            elif hasattr(value, 'get_absolute_url'):
                context[key] = u'<a href="%s">%s</a>' % (
                    value.get_absolute_url(), unicode(value))
            else:
                context[key] = value

        return context['text'] % context

    def render_template(self, viewer=None, view=None):
        context = self.get_context()
        context.update({
            'viewer': viewer,
            'view': view,
        })

        suffix = '.html'
        template_name = 'subscription/notifications/%s%s' % (
            context['template'], suffix)

        return template.loader.render_to_string(template_name, context)

    def display(self, viewer=None, view=None):
        if hasattr(self, 'text'):
            return self.render_text(viewer, view)
        elif hasattr(self, 'wikitext'):
            return self.render_wiki(viewer, view)
        elif hasattr(self, 'template'):
            return self.render_template(viewer, view)

class Variable(object):
    def __init__(self, value):
        self.value = value

    def __getstate__(self):
        return self.value
    
    def __setstate__(self, state):
        self.value = state

class Lazy(Variable):
    def __init__(self, value):
        self.value = value
    
    def __getstate__(self):
        if isinstance(self.value, Model):
            natural_key = ContentType.objects.get_for_model(self.value).natural_key()
            return (
                'model',
                natural_key,
                self.value.pk
            )
        else:
            return self.value

    def __setstate__(self, state):
        if isinstance(state, tuple) and state[0] == 'model':
            cache_key = 'model%s%s' % (''.join(state[1]), state[2])
            value = cache.get(cache_key)
            if value is None:
                model_class = ContentType.objects.get_by_natural_key(
                    state[1][0], state[1][1]).model_class()
                value = model_class.objects.get(pk=state[2])
                cache.set(cache_key, value, 7*60)

            self.value = value
        else:
            self.value = state
