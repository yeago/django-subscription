from string import Formatter

from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType

from subscription.models import Subscription

class BaseBackend(object):
    def __call__(obj,*args,**kwargs):
        return obj(*args,**kwargs)

    def __init__(self,obj,text,dont_send_to=None,send_only_to=None,actor=None,\
        actor_display_other=None,actor_display_self=None,format_kwargs=None,**kwargs):
        # obj - Thing people are subscribed to
        # dont_send_to / send_only_to - useful maybe?
        # text - string you want to emit.
        # actor_display_other - How does the actor appear to others? <a href="">{{ user.username }}</a>
        # actor_display_self - How does the actor appear to self? aka "You"
        # format_kwargs - Will be applied to text a la: text.format(**format_kwargs)
        # **kwargs - Maybe you wrote a backend that wants more stuff than the above!!

        # CAREFUL: If you send a typo-kwarg it will just be sent to emit(), so no error will raise =(

        self.content_type = ContentType.objects.get_for_model(obj)
        self.kwargs = kwargs

        explicit_format_options = [i[1] for i in Formatter().parse(text)]
        subscription_kwargs = {'content_type': self.content_type, 'object_id': obj.pk}
        if send_only_to:
            subscription_kwargs.update({'user__in': send_only_to})
        for i in Subscription.objects.filter(**subscription_kwargs):
            if i.user in (dont_send_to or []):
                continue

            if send_only_to and i.user not in send_only_to:
                continue

            _format_kwargs = {}
            _format_kwargs.update(format_kwargs or {})
            display_text = "%s" % text
            if "actor" in explicit_format_options:
                _format_kwargs.update({'actor': actor_display_other})
                if i.user == actor:
                    _format_kwargs.update({'actor': actor_display_self})

            text = text.format(**_format_kwargs) # Emit, somehow.
            self.emit(i.user,text,**kwargs)

    def emit(self,user,text,**kwargs):
        raise NotImplementedError("Override this!")

class SimpleEmailBackend(BaseBackend):
    def emit(self,user,text,**kwargs):
        if not user.email:
            return

        send_mail(self.get_subject(),text,None,[user.email])

    def get_subject(self):
        return "Here's a subject!"
