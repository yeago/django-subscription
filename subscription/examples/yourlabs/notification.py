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
    """
    A notification class is a type of notification.
    A notification instance is an actual notification.

    A notification should hold all the variables and methods necessary from
    emiting to rendering, because it is responsible of emiting and rendering.

    You can use this class without creating your own subclass. However, it is a
    good practice to encapsulate all notification specific code in a
    Notification subclass.
    """

    def emit(self, queues=None):
        """
        This is one of the most important methods. It is responsible for
        deciding what backends should it emit to and with what arguments - from
        meta data to subscribers whom should recieve the notification.

        If it should emit to multiqueue backends, then it's also responsible
        for deciding which queues it should emit to.
        """
        local_queues = getattr(self, 'queues', None)
        if queues is None and local_queues:
            queues = self.queues

        if queues:
            for backend_module in subscription.get_backends().values():
                backend_module().emit(self, queues)

    def __init__(self, **kwargs):
        """
        Any keyword arguments passed to the constructor is set as an instance variable.

        For example:
        >>> n=Notification(timestamp=1324629214, foo='bar')
        >>> n.timestamp
        1324629214
        >>> n.sent_at
        datetime.datetime(2011, 12, 23, 2, 33, 34)
        >>> n.foo
        'bar'

        Note that 'timestamp' and 'sent_at' have a little shortcut implemented
        in __setattr__ method of this class. When 'timestamp' is set, 'sent_at'
        is automatically set to the equivalent datetime value. And vice-versa:

        >>> n=Notification(sent_at=datetime.datetime(2011, 12, 23, 2, 33, 34))
        >>> n.sent_at
        datetime.datetime(2011, 12, 23, 2, 33, 34)
        >>> n.timestamp
        1324629214.0

        This is because dating is so important when managing notifications that
        it has been made so easy to work with. If you don't set either of
        sent_at or timestamp then the value will be generated when the
        notification is pickled.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __setattr__(self, key, value):
        """
        This is a magical python method which is called when an instance attribute
        is set. For example, notification.foo = 'bar' or 
        setattr(notfication, 'foo', 'bar') calls: 
        notification.__setattr__('notification', 'bar')

        It makes 'sent_at' when setting 'timestamp', and vice-versa.
        """
        actual_value = getattr(value, 'value', value)

        if key == 'timestamp':
            self.__dict__['sent_at'] = datetime.datetime.fromtimestamp(
                actual_value)
        elif key == 'sent_at':
            self.__dict__['timestamp'] = time.mktime(actual_value.timetuple())
        
        self.__dict__[key] = value

    def __getattribute__(self, name):
        """
        Note that if an attribute contains a Variable instance (defined later
        in this script) then it will return the value held by this variable
        instance. For example:

        >>> n=Notification(foo=Variable('bar'))
        >>> n.foo
        'bar'

        Don't worry about Variable too much for know, it is detailled further
        in this document.
        """
        value = object.__getattribute__(self, name)

        if isinstance(value, Variable):
            return value.value

        return value

    def __getattr__(self, name):
        """
        This is a magical python method which is called when a real instance
        attribute is retrieved. For example with notification.foo or
        getattr(notification, 'foo'): __getattr__('foo') is called, If the
        attribute exist, it calls __getattribute__. Otherwise throws an
        attribute error. Which is the default python behaviour. The only
        exception here is that it supports *_variable magical attribute.

        As you've seen in __getattribute__ docblock, Variable instances are
        abstracted away from the day to day usage of notification instances.
        But if you really want to get the variable instance, suffix the
        variable name with _variable:

        >>> n=Notification(foo=Variable('bar'))
        >>> n.foo
        'bar'
        >>> n.foo_variable
        <subscription.examples.yourlabs.notification.Variable at 0x2108cd0>
        """
        if '_variable' in name:
            name = '_'.join(name.split('_')[:-1])
            return object.__getattribute__(self, name)
        else:
            raise AttributeError

    def __getstate__(self):
        """
        This method is a standard method called by pickle when an object is
        pickled. Using pickle to save/restore notification instances as text si
        what allows such freedom in structuring your notification classes - the
        opposite is a django model, where only pre-defined attributes can be
        saved and restored.

        Rendering at pickle time is an interresting debate. Storing the
        rendered notification is an obvious performance gain when the
        notification is retrieved. Of course the downside is that it is less
        flexible, what if an object changes between the storage and the
        retrieval of a notification: the text will be obsolete.

        If the notification has the 'lazy' attribute set to True, then the
        notification will be pickled non-rendered, and will have to be rendered
        when it is displayed.
        """
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
        """
        Rendering may need a context. This method property is responsible for
        wrapping around and caching the result of get_context().
        """
        if not hasattr(self, '_context'):
            self._context = self.get_context()
        return self._context

    def get_context(self):
        """
        This method iterates over the instance attributes, and adds it to a
        dict. If an instance attribute is a variable, it will add the Variable
        value to the dict rather than the Variable instance itself.
        """
        context = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Variable):
                value = value.value
            context[key] = value
        return context

    def render_text(self, viewer=None, view=None):
        """
        Render a notification from a string. To use this method, it is required
        for the notification to have a 'text' attribute. Example:

        >>> n=Notification(text='%(author)s commented %(object)s', author='foo', object='bar')
        >>> n.render_text()
        'foo commented bar'

        There are a couple of special hooks: viewer and get_absolute_url.

        If viewer is set, and that one the context variables is equal to the
        viewer, then it will render as 'you':

        >>> from django.contrib.auth.models import User
        >>> n=Notification(text='%(author)s commented %(object)s', author=User.objects.get(username='james'), object=User.objects.get(username='steve'))
        >>> n.render_text()
        u'<a href="/users/james/">james</a> commented <a href="/users/steve/">steve</a>'
        >>> n.render_text(viewer=User.objects.get(username='james'))
        u'you commented <a href="/users/steve/">steve</a>'
        >>> n.render_text(viewer=User.objects.get(username='steve'))
        u'<a href="/users/james/">james</a> commented you'

        If you really want to render as text, then set the 'view' argument to
        'text':
        >>> n.render_text(view='text')
        'james commented steve'

        You got it, rendering is better when both the "viewer" (who is going to
        read it) and "view" (where is it going to be displayed) are specified.
        """
        context = self.get_context()

        for key, value in context.items():
            if viewer is not None and value == viewer:
                context[key] = u'you'
            elif hasattr(value, 'get_absolute_url') and \
                view != 'text':
                context[key] = u'<a href="%s">%s</a>' % (
                    value.get_absolute_url(), unicode(value))
            else:
                context[key] = value

        return context['text'] % context

    def render_template(self, viewer=None, view=None):
        """
        Render the notification from a template. To use this method, the
        notification is required to have a 'template' attribute.

        For forward compatibility, it is asked to *not* specify the suffix of
        the template in the template attribute. For example:

        >>> c = Comment(user=User.objects.get(pk=1), comment='hi', content_object=User.objects.get(pk=2), site_id=1)
        >>> c.save()
        >>> n = Notification(content=c.content_object, actor=c.user, template='comment')
        >>> n.render_template()
        u'\n\n            \n \n    <img src="http://www.gravatar.com/avatar/ab59525c7bd17926b4f2b57f23255580/?s=16" alt="james" width="16" height="16" />\n     \n            \n\n    \n        <a href="/users/james/">james</a>\n    \n\n    \n        \n            posted on <a href="/users/steve/">steve</a>\'s wall\n        \n    \n\n\nNone\n\n'

        Now you can see that the Notification instanciation takes really boring
        argument. And it's not nicely picklable as is, content and actor should
        be passed as Lazy variables for performance boost and flexibility. See
        how the CommentNotification class from yourlabs/apps/comments module is
        implemented and used.
        """
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
        """
        Of course, text and template notifications can be mixed in a
        notification list. This method abstracts the call to render_*().
        """
        if hasattr(self, 'text'):
            return self.render_text(viewer, view)
        elif hasattr(self, 'template'):
            return self.render_template(viewer, view)

class Variable(object):
    """
    This simple class holds a value in a picklable fashion. Consider it as the
    'interface' supported by the Notification class for your complex variable
    needs.

    See the next class, Lazy(Variable), for a cool example.
    """
    def __init__(self, value):
        self.value = value

    def __getstate__(self):
        return self.value
    
    def __setstate__(self, state):
        self.value = state

class Lazy(Variable):
    """
    This class holds a value. But if the value is a model, then it gets
    interresting. It will pickle as a tuple of ('model',
    'naturalContentTypeKey', pk). And the object is loaded when it is
    unpickled. Of course, the caching in __setstate__ which is called on
    unpickle is the awesome performance boost. If 100 notifacations are
    displayed with the same model then cache is likely to be used 99 times. It
    also acts as a crude 'identity map' in a way.
    """
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
