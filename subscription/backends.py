import time
import datetime
import json
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from .client import get_cache_client

from subscription.models import Subscription

ACTSTREAM_PROPERTIES = [
    'published',
    'actor',
    'target',
    'object',
]

class BaseBackend(object):
    def __call__(obj, *args, **kwargs):
        return obj(*args, **kwargs)

    def __init__(self, verb, subscribers_of=None, dont_send_to=None, send_only_to=None,
            emitter_class=None, spec=None, **kwargs):
        """
        Spec: http://activitystrea.ms/head/json-activity.html

        - subscribers_of - Thing people are subscribed to
        - dont_send_to / send_only_to - useful maybe?
        - **kwargs - Maybe you wrote a backend that wants more stuff than the above!!

        CAREFUL: If you send a typo-kwarg it will just be sent to emit(), so no error will raise =(
        """
        spec = spec or {}
        if emitter_class:
            emitter = emitter_class(verb=verb, **kwargs)
            for prop in ACTSTREAM_PROPERTIES:
                if getattr(emitter, prop, None):
                    spec[prop] = getattr(emitter, prop)

        self.kwargs = kwargs
        if not subscribers_of:
            for recipient in send_only_to:
                self.emit(recipient, spec, **kwargs)
            return

        self.content_type = ContentType.objects.get_for_model(subscribers_of)
        subscription_kwargs = {
            'content_type': self.content_type.pk,
            'object_id': subscribers_of.pk
        }
        if send_only_to:
            subscription_kwargs.update({'user__in': send_only_to})

        for i in Subscription.objects.filter(**subscription_kwargs):
            if i.user in (dont_send_to or []):
                continue

            if send_only_to and i.user not in send_only_to:
                continue
            self.emit(i.user, spec, **kwargs)

    def emit(self, user, spec, **kwargs):
        raise NotImplementedError("Override this!")


class ActStream(BaseBackend):
    def emit(self, user, spec, **kwargs):
        conn = get_cache_client()
        if not spec.get("published"):
            spec['published'] = int(time.mktime(datetime.datetime.now().timetuple()))
        conn.lpush("actstream::%s::undelivered" % user.pk, json.dumps(spec))


class SimpleEmailBackend(BaseBackend):
    def emit(self, user, text, **kwargs):
        if not user.email:
            return

        send_mail(self.get_subject(),text,None,[user.email])

    def get_subject(self):
        return "Here's a subject!"
