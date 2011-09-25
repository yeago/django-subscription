from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_was_posted

from subscription.examples.yourlabs import notifications
from subscription.models import Subscription
import subscription

class CommentNotification(notifications.TextNotification):
    def __init__(self, comment):
        self.text = '%(poster)s commented on %(content)s'
        self.content = notifications.Lazy(comment.content_object)
        self.poster = notifications.Lazy(comment.user)

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
            models.Q(
                subscription__content_type=content_ct,
                subscription__object_id=self.content.pk
            ) |
            models.Q(
                subscription__content_type=poster_ct,
                subscription__object_id=self.poster.pk
            )
        ).exclude(self.poster).distinct()

def comments_subscription(sender, **kwargs):
    comment = kwargs.pop('comment')

    if comment.user:
        Subscription.objects.subscribe(comment.user, comment.content_object)
        CommentNotification(comment).emit()
comment_was_posted.connect(comments_subscription)
