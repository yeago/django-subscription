from django.core.cache import cache
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType

class Variable(object):
    def __init__(self, value):
        self.value = value

    def __getstate__(self):
        return self.value
    
    def __setstate__(self, state):
        self.value = state

class Lazy(Variable):
    def __init__(self, value):
        self.value = value
    
    def __getstate__(self):
        if isinstance(self.value, Model):
            natural_key = ContentType.objects.get_for_model(self.value).natural_key()
            return (
                'model',
                natural_key,
                self.value.pk
            )
        else:
            return self.value

    def __setstate__(self, state):
        if isinstance(state, tuple) and state[0] == 'model':
            cache_key = 'model%s%s' % (''.join(state[1]), state[2])
            value = cache.get(cache_key)
            if value is None:
                model_class = ContentType.objects.get_by_natural_key(
                    state[1][0], state[1][1]).model_class()
                value = model_class.objects.get(pk=state[2])
                cache.set(cache_key, value, 7*60)

            self.value = value
        else:
            self.value = state
