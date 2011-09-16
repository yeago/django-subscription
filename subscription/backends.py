from string import Formatter

from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import trans_real
from django.conf import settings

from subscription.models import Subscription

class BaseBackend(object):
    def __call__(obj,*args,**kwargs):
        return obj().emit(*args,**kwargs)

    def emit(self,text,subscribers_of=None,dont_send_to=None,send_only_to=None,actor=None,
            actor_display_other=None,actor_display_self=None,format_kwargs=None, **kwargs):

        # backward compatibility stuff
        if actor_display_other:
            self.actor_display_other = actor_display_other
        if actor_display_self:
            self.actor_display_self = actor_display_self
       
        # todo: port this to proper docstring...
        # subscribers_of - Thing people are subscribed to
        # dont_send_to / send_only_to - useful maybe?
        # text - string you want to emit.
        # actor_display_other - How does the actor appear to others? <a href="">{{ user.username }}</a>
        # actor_display_self - How does the actor appear to self? aka "You"
        # format_kwargs - Will be applied to text a la: text.format(**format_kwargs)
        # **kwargs - Maybe you wrote a backend that wants more stuff than the above!!

        # CAREFUL: If you send a typo-kwarg it will just be sent to emit(), so no error will raise =(

        self.kwargs = kwargs
        
        if send_only_to and not subscribers_of:
            for recipient in send_only_to:
                self.emit(recipient, 
                    self.user_render(actor, text, user, format_kwargs),
                    **kwargs)

            return

        self.content_type = ContentType.objects.get_for_model(subscribers_of)
        subscription_kwargs = {'content_type': self.content_type, 'object_id': subscribers_of.pk}
        if send_only_to:
            subscription_kwargs.update({'user__in': send_only_to})

        for i in Subscription.objects.filter(**subscription_kwargs):
            if i.user in (dont_send_to or []):
                continue

            if send_only_to and i.user not in send_only_to:
                continue

            format_kwargs['actor'] = self.get_user_actor_display(i.user, actor)
            user_text = self.user_render(actor, text, i.user, format_kwargs)

            self.user_emit(i.user,user_text,**kwargs)

    def get_user_language_code(self, user):
        """
        Override to get the language from the user's profile if you want.
        """
        from django.conf import settings
        return settings.LANGUAGE_CODE

    def get_user_translation(self, user):
        """
        Convenience method which you probably do not want to override
        """
        from django.conf import settings
        if settings.USE_I18N:
            return trans_real.translation(self.get_user_language_code(user))
        else:
            return None

    def process_user_format_kwargs(self, user, format_kwargs):
        """
        Implement your own format_kwargs processor here.
        """
        return format_kwargs

    def get_user_actor_display(self, user, actor):
        """
        Use actor_display_* if specified in the constructor. Otherwise:
        - if actor is the user:
            - if translation: translated 'you'
            - else: just 'you'
        - else: a link to the actor using actor.get_absolute_url
        """
        t = self.get_user_translation(user)
        if user == actor:
            if hasattr(self, 'actor_display_self'):
                return self.actor_display_self

            if t:
                return t.gettext('You')
            else:
                return 'You'
        else:
            if hasattr(self, 'actor_display_other'):
                return self.actor_display_other
            else:
                return u'<a href="%s">%s</a>' % (
                    actor.get_absolute_url(),
                    actor.username,
                )

    def user_render(self, actor, text, user, format_kwargs):
        format_kwargs = self.process_user_format_kwargs(actor, text, user, format_kwargs)
        t = self.get_user_translation(user)
        if t:
            print t.gettext(text), format_kwargs
            text = t.gettext(text) % format_kwargs
        else:
            text = text % format_kwargs
        return text

    def user_emit(self,user,text,**kwargs):
        raise NotImplementedError("Override this!")

class SimpleEmailBackend(BaseBackend):
    def emit(self,user,text,**kwargs):
        if not user.email:
            return

        send_mail(self.get_subject(),text,None,[user.email])

    def get_subject(self):
        return "Here's a subject!"
