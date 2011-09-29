import datetime
import logging

try:
   import cPickle as pickle
except:
   import pickle

logger = logging.getLogger('redis')

import redis

import base
from subscription.examples.yourlabs.settings import *

class RedisBackend(base.BaseBackend):
    def __init__(self, prefix='subscription:'):
        self.prefix = prefix

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = redis.Redis()
        return self._redis

    def queue(self, notification, queue):
        logger.debug('queuing to %s: %s' % (queue, notification))
        self.redis.lpush(self.prefix + queue, pickle.dumps(notification))

    def move_queue(self, source, destination):
        logger.debug('moving to %s: %s' % (source, destination))

        source = self.prefix + source
        destination = self.prefix + destination

        notifications = self.redis.lrange(source, 0, -1)

        for notification in notifications:
            self.redis.lpush(destination, notification)
            self.redis.lrem(source, notification)

    def get_notifications(self, queue, limit=-1):
        queue = self.prefix + queue

        if limit > 0:
            queue_limit = limit - 1
        elif limit == 0:
            return []
        else:
            queue_limit = limit

        return [pickle.loads(n) for n in self.redis.lrange(queue, 0, queue_limit)]

    def count_notifications(self, queue):
        queue = self.prefix + queue
        return self.redis.llen(queue)
