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
    def __getstate__(self):
        if isinstance(self.value, Model):
            key = ContentType.objects.get_for_model(self.value).natural_key()
            return (
                'model',
                key,
                self.value.pk
            )
        else:
            return self.value

    def __setstate__(self, state):
        if isinstance(state, tuple) and state[0] == 'model':
            model_class = ContentType.objects.get_by_natural_key(
                state[1][0], state[1][1]).model_class()
            self.value = model_class.objects.get(pk=state[2])
        else:
            self.value = state
