import time
from string import Formatter

from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType

from subscription.models import Subscription

class BaseBackend(object):
    def __call__(obj, *args, **kwargs):
        return obj(*args, **kwargs)

    def __init__(self, instance, subscribers_of=None, dont_send_to=None, send_only_to=None,\
        format_kwargs=None, **kwargs):
        # subscribers_of - Thing people are subscribed to
        # dont_send_to / send_only_to - useful maybe?
        # text - string you want to emit.
        # **kwargs - Maybe you wrote a backend that wants more stuff than the above!!
        # CAREFUL: If you send a typo-kwarg it will just be sent to emit(), so no error will raise =(

        spec = self.create_spec(instance)

        self.kwargs = kwargs

        if not subscribers_of:
            for recipient in send_only_to:
                self.emit(recipient, spec, **kwargs)
            return

        self.content_type = ContentType.objects.get_for_model(subscribers_of)
        subscription_kwargs = {'content_type':
            self.content_type.pk,
            'object_id': subscribers_of.pk}
        if send_only_to:
            subscription_kwargs.update({'user__in': send_only_to})

        for i in Subscription.objects.filter(**subscription_kwargs):
            if i.user in (dont_send_to or []):
                continue

            if send_only_to and i.user not in send_only_to:
                continue
            self.emit(i.user, spec, **kwargs)

    def create_spec(self, verb, instance):
        """
        http://activitystrea.ms/head/json-activity.html

        Override this puppy for conditional checking. Right now it scarfs
        comments and comment-like things.
        """
        return {
            'published': time.mktime(instance.created.timetuple()),
            'target': {
                'objectId': instance.object_id,
                'objectType': instance.content_type_id,
                'url': instance.content_object.get_absolute_url(),
                'displayName': instance.content_object,
            },
            'verb': verb,
            'actor': {
                'id': instance.user_id,
            },
            'object': {
                'id': instance.pk,
                'url': instance.get_absolute_url(),
            }
        }

    def emit(self,user,text,**kwargs):
        raise NotImplementedError("Override this!")

class SimpleEmailBackend(BaseBackend):
    def emit(self,user,text,**kwargs):
        if not user.email:
            return

        send_mail(self.get_subject(),text,None,[user.email])

    def get_subject(self):
        return "Here's a subject!"
