from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

try:
    from django.utils.module_loading import import_by_path
except ImportError:
    from django.utils.importlib import import_module
    def import_by_path(path):
        i = path.rfind('.')
        module, attr = path[:i], path[i+1:]
        try:
            mod = import_module(module)
        except ImportError, e:
            raise ImproperlyConfigured('Error importing subscription backend %s: "%s"' % (path, e))
        except ValueError, e:
            raise ImproperlyConfigured('Error importing subscription backends. Is SUBSCRIPTION_BACKENDS a correctly defined dictionary?')
        try:
            return getattr(mod, attr)
        except AttributeError:
            raise ImproperlyConfigured('Module "%s" does not define a "%s" subscription backend' % (module, attr))

def get_backends():
    backends = {}
    for backend_name, backend_path in settings.SUBSCRIPTION_BACKENDS.items():
        backends[backend_name] = import_by_path(backend_path)
    if not backends:
        raise ImproperlyConfigured('No subscription backends have been defined. Does SUBSCRIPTION_BACKENDS contain anything?')
    return backends
