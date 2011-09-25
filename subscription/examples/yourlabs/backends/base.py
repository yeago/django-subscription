import datetime

from django.utils.importlib import import_module
from django.utils import simplejson
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from subscription.models import Subscription
from subscription.examples.yourlabs.settings import *


class BaseBackend(object):
    def emit(self, notification, subscribers_of=None, dont_send_to=None, 
        send_to=None, state=NOTIFICATION_STATES[0], 
        queue=NOTIFICATION_QUEUES[0]):

        if send_to is None:
            send_to = []

        send_to = list(send_to)
        if subscribers_of:
            ct = ContentType.objects.get_for_model(subscribers_of)
            send_to += list(User.objects.filter(
                subscription__content_type=ct, 
                subscription__object_id=subscribers_of.pk))

        notification.sent_at = datetime.datetime.now()

        for user in send_to:
            if user in dont_send_to:
                continue

            self.user_emit(user, notification, state, queue)

    def user_emit(self, user, notification, state=NOTIFICATION_STATES[0], 
        queue=NOTIFICATION_QUEUES[0]):
        raise NotImplementedError()

    def push_state(self, user, 
        state=NOTIFICATION_STATES[0], queue=NOTIFICATION_QUEUES[0]):
        raise NotImplementedError()

    def get_notifications(self, user, 
        state=NOTIFICATION_STATES[0], queue=NOTIFICATION_QUEUES[0],
        limit=-1):
        raise NotImplementedError()

    def count_notifications(self, user, state=NOTIFICATION_STATES[0], 
        queue=NOTIFICATION_QUEUES[0]):
        raise NotImplementedError()

    def serialize(self, user, notification):
        cls = notification.__class__
        return simplejson.dumps((
            '%s.%s' % (cls.__module__, cls.__name__),
            notification.to_dict(user),
        ))

    def unserialize(self, data):
        data = simplejson.loads(data)

        tmp = data[0].split('.')
        cls = tmp.pop()
        module = '.'.join(tmp)
        cls = getattr(import_module(module), cls)

        return cls(**data[1])
