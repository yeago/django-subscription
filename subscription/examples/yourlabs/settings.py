from django.conf import settings

if hasattr(settings, 'SUBSCRIPTION_NOTIFICATION_QUEUES'):
    NOTIFICATION_QUEUES = settings.SUBSCRIPTION_NOTIFICATION_QUEUES
else:
    NOTIFICATION_QUEUES = ['default']

if hasattr(settings, 'SUBSCRIPTION_NOTIFICATION_STATES'):
    NOTIFICATION_STATES = settings.SUBSCRIPTION_NOTIFICATION_STATES
else:
    NOTIFICATION_STATES = ['undelivered', 'unacknowledged', 'acknowledged']

if hasattr(settings, 'LANGUAGE_CODE'):
    LANGUAGE_CODE = settings.LANGUAGE_CODE
else:
    LANGUAGE_CODE = 'en'

if hasattr(settings, 'USE_I18N'):
    USE_I18N = settings.USE_I18N
else:
    USE_I18N = False
