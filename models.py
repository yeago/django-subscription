from django.db import models

from django.core.mail import send_mail
from django.dispatch import Signal
from django.conf import settings
from django.template import loader, RequestContext

from django.contrib.contenttypes.models import ContentType
from django.contrib import comments
from django.contrib.comments import signals
from django.contrib.sites.models import Site
from django.contrib.contenttypes import generic

class Subscription(models.Model):
    user = models.ForeignKey('auth.User')
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    timestamp = models.DateTimeField(editable=False)
    def save(self,*args,**kwargs):
        if not self.timestamp:
            import datetime
            self.timestamp = datetime.datetime.now()
        super(Subscription,self).save(*args,**kwargs)

def email_comment(**kwargs):
    comment = kwargs.pop('comment')
    request = kwargs.pop('request')

    site = Site.objects.get(id=settings.SITE_ID)

    supress_email_field = getattr(settings,'SUBSCRIPTION_EMAIL_SUPRESS_PROFILE_FIELD','no_email')
    t = loader.get_template('comments/email_comment_template.html')

    subscriptions = Subscription.objects.filter(content_type=comment.content_type,\
		    object_id=comment.object_pk).exclude(user=comment.user)

    for i in subscriptions:
        if getattr(i.user.get_profile(),supress_email_field,False):
            continue

        c = {
            'domain': site.domain,
            'site_name': site.name,
            'c': comment,
            'delete': i.user.has_perm('comments.delete_comment'),
            'subscription': i,
        }
        send_mail(("%s - Comment on %s") % (site.name,comment.content_object), \
			t.render(RequestContext(request,c)), None, [i.user.email])

def auto_subscribe(**kwargs):
    comment = kwargs.pop('comment')
    auto_subscribe_field = getattr(settings,'SUBSCRIPTION_AUTOSUBSCRIBE_PROFILE_FIELD','auto_subscribe')
    if getattr(comment.user.get_profile(),auto_subscribe_field,True):
        Subscription.objects.get_or_create(user=comment.user,content_type=comment.content_type,object_id=comment.object_pk)

Comment = comments.get_model()

signals.comment_was_posted.connect(email_comment, sender=Comment)
signals.comment_was_posted.connect(auto_subscribe, sender=Comment)
my_signal = Signal()
