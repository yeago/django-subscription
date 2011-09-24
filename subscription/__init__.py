from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

def load_backend(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise 
        raise ImproperlyConfigured('Error importing subscription backend %s: "%s"' % (path, e))
    except ValueError, e:
        raise ImproperlyConfigured('Error importing subscription backends. Is SUBSCRIPTION_BACKENDS a correctly defined dictionary?')
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" subscription backend' % (module, attr))

    return cls

def get_backends():
    from django.conf import settings
    backends = {}
    for backend_name, backend_path in settings.SUBSCRIPTION_BACKENDS.items():
        backends[backend_name] = load_backend(backend_path)

    if not backends:
        raise ImproperlyConfigured('No subscription backends have been defined. Does SUBSCRIPTION_BACKENDS contain anything?')

    return backends
