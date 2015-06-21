import datetime
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from subscription.base import get_backends
from django.db.models.query import QuerySet

from model_utils.managers import PassThroughManager

class StreamAcknowledgeProfileMixin(object):
    """
    You must add this to your userprofile:
    stream_last_acknowledged = models.DateTimeField(null=True, blank=True)
    """
    def get_stream_acknowledged(self):
        """
        Last time they checked their notifications

        This assumes a datetime field on the userprofile
        """
        return self.stream_last_acknowledged

    def stream_pending_acknowledgements(self, date):
        if not self.stream_last_acknowledged or self.stream_last_acknowledged <= date:
            return True
        return False


class SubscriptionQuerySet(QuerySet):
    _subscription_exclude = []
    _subscription_to = []
    _subscription_of = None

    def _clone(self, **kwargs):
        clone = super(SubscriptionQuerySet, self)._clone(**kwargs)
        clone._subscription_to = self._subscription_to
        clone._subscription_exclude = self._subscription_exclude
        clone._subscription_of = self._subscription_of
        clone.__dict__.update(kwargs)
        return clone

    def of(self, instance):
        clone = self._clone()
        ct = ContentType.objects.get_for_model(instance)
        clone._subscription_of = Subscription.objects.filter(content_type=ct.pk, object_id=instance.pk)
        return clone

    def to(self, user):
        clone = self._clone()
        try:
            iter(user)
            clone._subscription_to.extend(user)
        except TypeError:
            clone._subscription_to.append(user)
        return clone

    def not_to(self, user):
        clone = self._clone()
        try:
            iter(user)
            clone._subscription_exclude.extend(user)
        except TypeError:
            clone._subscription_exclude.append(user)
        return clone

    def subscribe(self, user, obj):
        ct = ContentType.objects.get_for_model(obj)
        Subscription.objects.get_or_create(content_type=ct,object_id=obj.pk,user=user)

    def emit(self, *args, **kwargs):
        clone = self._clone()

        backend = kwargs.pop('backend',None) or None
        for backend_module in get_backends().values():
            if backend and not backend_module == backend:
                continue
            for item in clone._subscription_to:
                if item in clone._subscription_exclude:
                    continue
                backend_module(item, *args, **kwargs)
            for item in clone._subscription_of or []:
                if item.user in clone._subscription_to or item.user in clone._subscription_exclude:
                    continue
                backend_module(item.user, *args, **kwargs)


class Subscription(models.Model):
    user = models.ForeignKey('auth.User')
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    timestamp = models.DateTimeField(editable=False,default=datetime.datetime.now)
    objects = PassThroughManager.for_queryset_class(SubscriptionQuerySet)()
    class Meta:
        db_table ="subscription"

"""
Seems sensible to auto-subscribe people to objects they comment on.

Just send this with the comment_was_posted signal

def auto_subscribe(**kwargs):
    comment = kwargs.pop('comment')
    auto_subscribe_field = getattr(settings,'SUBSCRIPTION_AUTOSUBSCRIBE_PROFILE_FIELD','auto_subscribe')
    if getattr(comment.user.get_profile(),auto_subscribe_field,True):
        Subscription.objects.subscribe(user,comment.content_object)

comment_was_posted.connect(auto_subscribe, sender=CommentModel)
"""

"""
Make abstract, turn into emit backend
#comment_was_posted.connect(email_comment, sender=CommentModel)

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
        if not i.user.email:
            continue

        send_mail(("%s - Comment on %s") % (site.name,comment.content_object), \
               t.render(RequestContext(request,c)), None, [i.user.email])
"""
