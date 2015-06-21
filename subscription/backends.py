import time
import datetime
import json
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from .client import get_cache_client
from .cluster import cluster_specs

from subscription.models import Subscription
from django.conf import settings

DEFAULT_ACTSTREAM_PROPERTIES = [
    'published',
    'actor',
    'target',
    'object',
]

class BaseBackend(object):
    def __call__(obj, *args, **kwargs):
        return obj(*args, **kwargs)

    def __init__(self, user, verb, emitter_class=None, spec=None, **kwargs):
        """
        Verb, Spec: http://activitystrea.ms/head/json-activity.html
        - **kwargs - Maybe you wrote a backend that wants more stuff than the above!!

        CAREFUL: If you send a typo-kwarg it will just be sent to emit(), so no error will raise =(
        """
        spec = spec or {}
        spec['verb'] = verb
        for prop in DEFAULT_ACTSTREAM_PROPERTIES:
            if kwargs.get(prop):
                spec[prop] = kwargs[prop]

        if hasattr(settings, 'SUBSCRIPTION_ACTSTREAM_PROPERTIES'):
            ## The user wanted to add more things to the spec
            for prop in settings.SUBSCRIPTION_ACTSTREAM_PROPERTIES:
                if kwargs.get(prop):
                    spec[prop] = kwargs[prop]


        if emitter_class:
            emitter = emitter_class(spec)
            for prop in ACTSTREAM_PROPERTIES:
                if getattr(emitter, prop, None):
                    spec[prop] = getattr(emitter, prop)

        self.kwargs = kwargs
        cluster_specs([spec])  # Try it out. If shit goes wrong it wasn't meant to be.
        self.emit(user, spec, **kwargs)

    def emit(self, user, spec, **kwargs):
        raise NotImplementedError("Override this!")


class UserStream(BaseBackend):
    def emit(self, user, spec, **kwargs):
        conn = get_cache_client()
        if not spec.get("published"):
            spec['published'] = int(time.mktime(datetime.datetime.now().timetuple()))
        conn.lpush("actstream::%s" % user.pk, json.dumps(spec))


class SimpleEmailBackend(BaseBackend):
    def emit(self, user, text, **kwargs):
        if not user.email:
            return

        send_mail(self.get_subject(),text,None,[user.email])

    def get_subject(self):
        return "Here's a subject!"
