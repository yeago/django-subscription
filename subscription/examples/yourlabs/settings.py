from django.conf import settings

REDIS_PREFIX = getattr(settings, 'SUBSCRIPTION_REDIS_PREFIX', 'default:')
