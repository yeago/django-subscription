from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_by_path
from django.conf import settings

def get_backends():
    backends = {}
    for backend_name, backend_path in settings.SUBSCRIPTION_BACKENDS.items():
        backends[backend_name] = import_by_path(backend_path)
    if not backends:
        raise ImproperlyConfigured('No subscription backends have been defined. Does SUBSCRIPTION_BACKENDS contain anything?')
    return backends
