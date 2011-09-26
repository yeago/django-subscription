from django.db.models import signals
from django.db.models import get_model

from subscription.models import Subscription
from subscription.examples.yourlabs import shortcuts
from subscription.examples.yourlabs.notification import Notification, Lazy

"""
Example usage, in your project put:

from subscription.examples.yourlabs.apps import actstream
actstream.signals.post_save.connect(actstream.subscribe_user_to_his_action, 
    sender=actstream.Action)
actstream.signals.post_save.connect(actstream.follow_lazy_template_notification,
    sender=actstream.Follow)
"""

Follow = get_model('actstream', 'follow')
Action = get_model('actstream', 'action')

def subscribe_user_to_his_action(sender, **kwargs):
    action = kwargs['instance']
    if action.actor.__class__.__name__ == 'User':
        Subscription.objects.subscribe(action.actor, action)

class FollowNotification(Notification):
    @classmethod
    def kwargs_factory(cls, follow, **kwargs):
        kwargs.update(
            actor=follow.user,
            content=follow.actor
        )
        return kwargs

    @property
    def queues(self):
        queues = []
        for subscriber in self.subscribers:
            queues.append('dropdown=friends,user=%s,undelivered' % subscriber.pk)
        return queues

def follow_lazy_template_notification(sender, instance=None, **kwargs):
    shortcuts.emit_lazy(FollowNotification, follow=instance, template='follow',
        subscribers=[instance.actor])
