import datetime

import redis

import base
from subscription.examples.yourlabs.settings import *


class RedisBackend(base.BaseBackend):
    def __init__(self, prefix='subscription'):
        self.prefix = prefix

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = redis.Redis()
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
            return
        
        next_state = NOTIFICATION_STATES[next_state_key]

        notifications = self.redis.lrange(
            self.get_key(user, state, queue), 0, -1)

        for notification in notifications:
            print "PUSH", self.get_key(user, next_state, queue), self.get_key(user, state, queue)
            self.redis.lpush(
                self.get_key(user, next_state, queue), notification)
            self.redis.lrem(self.get_key(user, state, queue), notification)

    def get_notifications(self, user, 
        state=NOTIFICATION_STATES[0], queue=NOTIFICATION_QUEUES[0],
        limit=-1):

        if limit > 0:
            queue_limit = limit - 1
        elif limit == 0:
            return []
        else:
            queue_limit = limit

        serialized_notifications = self.redis.lrange(
            self.get_key(user, state, queue), 0, queue_limit)

        result = []
        for serialized_notification in serialized_notifications:
            notification = self.unserialize(serialized_notification)
            notification.initial_state = state
            result.append(notification)
        
        return result

    def count_notifications(self, user, state=NOTIFICATION_STATES[0], 
        queue=NOTIFICATION_QUEUES[0]):
        return self.redis.llen(self.get_key(user, state, queue))

    def user_emit(self, user, notification, state=NOTIFICATION_STATES[0], 
        queue=NOTIFICATION_QUEUES[0]):
        
        if not hasattr(notification, 'timestamp'):
            notification.sent_at = datetime.datetime.now()

        self.redis.lpush(self.get_key(user, state, queue), 
            self.serialize(user, notification))
