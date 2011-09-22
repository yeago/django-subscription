from django.conf import settings

NOTIFICATION_QUEUES = getattr(settings, 'SUBSCRIPTION_NOTIFICATION_QUEUES',
    ['default'])

NOTIFICATION_STATES = getattr(settings, 'SUBSCRIPTION_NOTIFICATION_STATES', 
    ['undelivered', 'unacknowledged', 'acknowledged'])

LANGUAGE_CODE = getattr(settings, 'LANGUAGE_CODE', 'en')

USE_I18N = getattr(settings, 'USE_I18N', False)
