from django.conf import settings
from django.db.models import signals
from django.contrib.auth.models import User

from subscription.models import Subscription

APPS = settings.INSTALLED_APPS

if 'django.contrib.comments' in APPS:
    from django.contrib.comments.models import Comment
    from django.contrib.comments.signals import comment_was_posted

    def auto_subscribe_user_to_what_he_comments(sender, **kwargs):
        comment = kwargs.pop('comment')
        Subscription.objects.subscribe(comment.user, comment.content_object)
        emit_new_comment(comment)
    comment_was_posted.connect(auto_subscribe_user_to_what_he_comments)

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

if getattr(settings, 'USE_COMMENTS_AS_WALL', False):
    from django.contrib.comments.signals import comment_was_posted

    def auto_subscribe_user_to_himself(sender, **kwargs):
        user = kwargs.pop('instance')
        Subscription.objects.subscribe(user, user)
    signals.post_save.connect(auto_subscribe_user_to_himself, sender=User)

    def auto_subscribe_user_to_his_comments(sender, **kwargs):
        comment = kwargs.pop('comment')
        user = comment.user
        Subscription.objects.subscribe(user, comment)
    comment_was_posted.connect(auto_subscribe_user_to_his_comments)

if 'actstream' in APPS:
    from actstream.models import Follow, Action

    def auto_follow_notification(sender, **kwargs):
        emit_new_follower(kwargs['instance'].actor, kwargs['instance'].user)
    signals.post_save.connect(auto_follow_notification, sender=Follow)

    def auto_subscribe_user_to_his_actions(sender, **kwargs):
        action = kwargs['instance']
        if action.actor.__class__.__name__ == 'User':
            Subscription.objects.subscribe(action.actor, action)
    signals.post_save.connect(auto_subscribe_user_to_his_actions, sender=Action)

    def emit_new_follower(user, follower):
        Subscription.objects.emit(
            u'%(actor)s follows you',
            send_only_to=[user],
            actor=follower,
            queue='friends',
        )

if 'django_messages' in APPS:
    from django_messages.models import Message

    def auto_message_notification(sender, **kwargs):
        if not kwargs.get('created', False):
            return
        emit_new_message(kwargs['instance'])
    signals.post_save.connect(auto_message_notification, sender=Message)

    def emit_new_message(message):
        Subscription.objects.emit(
            u'%(actor)s sent you a %(target)s',
            send_only_to=[message.recipient],
            context={
                'message': message,
            },
            actor=message.sender,
            queue='chat',
        )
