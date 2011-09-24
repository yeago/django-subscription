import datetime
import time

from django.utils.importlib import import_module
from django.utils import simplejson
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.conf import settings

from redis import Redis
from subscription.models import Subscription

from settings import *
from exceptions import *

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
                subscription__content_type=ct, object_id=subscribers_of.pk))

        notification.sent_at = datetime.datetime.now()

        for user in send_to:
            if user in dont_send_to:
                continue

            self.user_emit(user, notification, state, queue)

    def user_emit(self, user, state, queue):
        raise NotImplementedError("Override this!")

class RedisBackend(BaseBackend):
    def __init__(self, prefix='subscription'):
        self.prefix = prefix

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = Redis()
        return self._redis

    def get_key(self, user, state, queue=NOTIFICATION_QUEUES[0]):
        if hasattr(user, 'pk'):
            user = user.pk

        return '%s::%s::%s::%s' % (
            self.prefix,
            user,
            state, 
            queue,
        )

    def get_timestamps_key(self, user, queue=NOTIFICATION_QUEUES[0]):
        if hasattr(user, 'pk'):
            user = user.pk

        return '%s::timestamps::%s::%s' % (self.prefix, user, queue)

    def push_state(self, user, 
        state=NOTIFICATION_STATES[0], queue=NOTIFICATION_QUEUES[0]):
        """
        Upgrade the state of a user's notification. For example, if 
        'undelivered' is above 'unacknowledged', then pushing all
        notifications from 'undelivered' to 'unacknowledged'::

            backend.push_state(user, 'undelivered')

        By default, states will be a list containing only the first state in
        settings.SUBSCRIPTION_NOTIFICATION_STATES.

        Note that this function is not totally safe. If the server 
        crashes between the copy and the delete then duplicate notifications
        will result.
        """
        next_state_key = NOTIFICATION_STATES.index(state) + 1

        if next_state_key + 1 > len(NOTIFICATION_STATES):
            raise CannotPushLastState(state, NOTIFICATION_STATES)
        
        next_state = NOTIFICATION_STATES[next_state_key]

        notifications = self.redis.lrange(
            self.get_key(user, state, queue), 0, -1)

        for notification in notifications:
            self.redis.lpush(
                self.get_key(user, next_state, queue), notification)
            self.redis.lrem(self.get_key(user, state, queue), notification)

    def get_last_notifications(self, user, queues=NOTIFICATION_QUEUES, 
        queue_limit=-1, states=[NOTIFICATION_STATES[0]], reverse=False,
        push=[NOTIFICATION_STATES[0]]):

        if queue_limit > 0:
            redis_queue_limit = queue_limit - 1
        else:
            redis_queue_limit = queue_limit

        result = {}
        for queue in queues:
            for state in states:
                if queue_limit > 0 and queue in result.keys():
                    if len(result[queue]['notifications']) >= queue_limit:
                        # enought for this queue
                        break

                serialized_notifications = self.redis.lrange(
                    self.get_key(user, state, queue), 0, redis_queue_limit)

                if queue not in result.keys():
                    result[queue] = {}
                    result[queue]['notifications'] = []

                for serialized_notification in serialized_notifications:
                    notification = self.unserialize(serialized_notification)
                    notification['initial_state'] = state
                    result[queue]['notifications'].append(notification)

                    if queue_limit > 0:
                        if len(result[queue]['notifications']) >= queue_limit:
                            # enought for this queue
                            break

            if reverse:
                result[queue]['notifications'].reverse()

        for queue in queues:
            result[queue]['counts'] = {
                'total': 0,
            }

            for s in NOTIFICATION_STATES:
                length = self.redis.llen(self.get_key(user, s, queue))
                result[queue]['counts'][s] = length
                result[queue]['counts']['total'] += length

            if push:
                for state in push:
                    self.push_state(user, state, queue)

        return result

    def get_all_notifications(self, user, states=NOTIFICATION_STATES, 
        queues=NOTIFICATION_QUEUES, order_by='timestamp', 
        push=[NOTIFICATION_STATES[0], NOTIFICATION_STATES[1]]):

        result = []
        for state in states:
            for queue in queues:
                serialized_notifications = self.redis.lrange(self.get_key(user, state, queue), 0, -1)
                for notification in serialized_notifications:
                    notification = self.unserialize(notification)
                    notification['initial_state'] = state
                    notification['queue'] = queue
                    result.append(notification)

        if order_by:
            result = sorted(result, key=lambda x: x[order_by])
        
        if push:
            for state in push:
                for queue in queues:
                    self.push_state(user, state, queue)

        return result

    def user_emit(self, user, notification, state=NOTIFICATION_STATES[0], 
        queue=NOTIFICATION_QUEUES[0]):
        
        if not hasattr(notification, 'timestamp'):
            notification.sent_at = datetime.datetime.now()

        self.redis.lpush(self.get_key(user, state, queue), 
            self.serialize(user, notification))

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

        return cls(user=user, **data[1])
