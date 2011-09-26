from django.db.models import Q
from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_was_posted
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

import subscription
from subscription.models import Subscription

from subscription.examples.yourlabs import shortcuts
from subscription.examples.yourlabs.notification import Notification, Lazy

class CommentNotification(Notification):
    @classmethod
    def kwargs_factory(cls, comment, **kwargs):
        kwargs.update(
            content=comment.content_object,
            poster=comment.user,
            sent_at=comment.submit_date,
        )
        return kwargs

    @property
    def queues(self):
        queues = []
        for subscriber in self.subscribers:
            queues.append('dropdown=chat,user=%s,undelivered' % subscriber.pk)
        return queues

    @property
    def subscribers(self):
        content_ct = ContentType.objects.get_for_model(self.content)
        poster_ct = ContentType.objects.get_for_model(self.poster)

        return User.objects.filter(
            Q(
                subscription__content_type=content_ct,
                subscription__object_id=self.content.pk
            ) |
            Q(
                subscription__content_type=poster_ct,
                subscription__object_id=self.poster.pk
            )
        ).exclude(pk=self.poster.pk).distinct()

def comments_subscription(sender, comment=None, **kwargs):
    if comment.user:
        Subscription.objects.subscribe(comment.user, comment.content_object)

# four examples to choose from ...
def comment_lazy_text_notification(sender, comment=None, **kwargs):
    if comment.user:
        shortcuts.emit_lazy(CommentNotification,
            comment=comment,
            text='%(poster)s commented on %(content)s')

def comment_lazy_template_notification(sender, **kwargs):
    comment = kwargs.pop('comment')
    if comment.user:
        shortcuts.emit_lazy(CommentNotification,
            comment=comment,
            template='new_comment').emit()

def comment_static_text_notification(sender, **kwargs):
    comment = kwargs.pop('comment')
    if comment.user:
        shortcuts.emit_static(CommentNotification,
            comment=comment,
            text='%(poster)s commented on %(content)s').emit()

def comment_static_template_notification(sender, **kwargs):
    comment = kwargs.pop('comment')
    if comment.user:
        shortcuts.emit_static(CommentNotification,
            comment=comment,
            template='new_comment').emit()
