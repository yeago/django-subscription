import time
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags

def model_to_spec(obj):
    spec = { 
        'objectId': obj.pk,
        'objectType': ContentType.objects.get_for_model(obj).pk,
        'displayName': "%s" % obj,
    }
    try:
        url = obj.get_absolute_url()
        spec['url'] = url
        spec['displayName'] = "<a href='%s'>%s</a>" % (url, strip_tags('%s' % obj))
    except AttributeError:
        pass
    return spec


class ModelEmitter(object):
    """
    Example emitter object which loosely converts django
    models into specs. Probably won't work perfectly out of
    the box, but that's why we subclass.
    """
    def __init__(self, kwargs):
        self.kwargs = kwargs

    def _generic(self, obj):
        if isinstance(obj, Model):
            return model_to_spec(obj)
        return obj

    @property
    def target(self):
        if self.kwargs.get('target'):
            return self._generic(self.kwargs['target'])

    @property
    def object(self):
        if self.kwargs.get('object'):
            return self._generic(self.kwargs['object'])

    @property
    def actor(self):
        if self.kwargs.get('actor'):
            return self._generic(self.kwargs['actor'])


class CommentEmitter(ModelEmitter):
    """
    Fun sample which you can use to beam a django.contrib.comments Comment
    """
    @property
    def published(self):
        time.mktime(self.kwargs['object'].submit_date.timetuple())

    @property
    def target(self):
        instance = self.kwargs['object']
        return self._generic(instance.content_object)

    @property
    def actor(self):
        return self._generic(self.kwargs['object'].user)
