from django.conf import settings
from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_was_posted

from subscription.models import Subscription

APPS = settings.INSTALLED_APPS

if 'django.contrib.comments' in APPS:
    def auto_comment(sender, **kwargs):
        comment = kwargs.pop('comment')
        Subscription.objects.subscribe(comment.user,comment.content_object)
        emit_new_comment(comment)
    comment_was_posted.connect(auto_comment, sender=Comment)
    
    def emit_new_comment(comment):
        Subscription.objects.emit(
            u'%(actor)s commented on %(target)s',
            subscribers_of=comment.content_object,
            dont_send_to=[comment.user],
            context={
                'comment': comment,
            },
            actor=comment.user,
            queue='chat',
        )
