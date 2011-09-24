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
        u'%(actor_display)s follows you',
        send_only_to=[user],
        queue='friends',
        context={'actor': follower},
    )

