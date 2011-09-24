from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_was_posted

from subscription.examples.yourlabs import notifications
from subscription.models import Subscription

def auto_subscribe_user_to_what_he_comments(sender, **kwargs):
    comment = kwargs.pop('comment')
    if comment.user:
        Subscription.objects.subscribe(comment.user, comment.content_object)
    emit_new_comment(comment)
comment_was_posted.connect(auto_subscribe_user_to_what_he_comments)

def emit_new_comment(comment):
    notifications.TextNotification(
        text=u'%(actor_display)s commented on %(object_display)s',
        format_kwargs={
            'actor': comment.user,
            'object': comment.content_object
        }
    ).emit(
        subscribers_of=comment.content_object,
        dont_send_to=[comment.user],
        queue='chat'
    )
