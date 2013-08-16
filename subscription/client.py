from django.conf import settings
try:
    from redis import Redis as RedisBase
except ImportError:
    class RedisBase(object):
        pass

class Redis(RedisBase):
    def __init__(self, **kwargs):
        kwargs = kwargs or {}
        if not 'port' in kwargs:
            kwargs['port'] = settings.REDIS_PORT
        if not 'host' in kwargs:
            kwargs['host'] = settings.REDIS_HOST
        if not 'db' in kwargs:
            kwargs['db'] = settings.REDIS_DB
        super(Redis,self).__init__(**kwargs)

def get_cache_client(**kwargs):
    return Redis(**kwargs)
