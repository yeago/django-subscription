import datetime

from django.utils.importlib import import_module
from django.utils import simplejson
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from subscription.models import Subscription
from subscription.examples.yourlabs.settings import *

class BaseBackend(object):
    def emit(self, notification, queues=None):
        if queues is None:
            queues = ['default']

        for queue in queues:
            self.queue(notification, queue, state)

    def queue(self, notification, queue):
        raise NotImplementedError()

    def move_queue(self, source, destination):
        raise NotImplementedError()

    def get_notifications(self, queue, limit=-1):
        raise NotImplementedError()

    def count_notifications(self, queue):
        raise NotImplementedError()
