from django import template

import subscription
from subscription.examples.yourlabs.settings import *

register = template.Library()

def subscription_yourlabs_widget(request, queue_limit=15):
    if not request.user.is_authenticated():
        return {}

    b = subscription.get_backends()['redis']()
    notification_list = b.get_last_notifications(request.user, 
        states=NOTIFICATION_STATES, queue_limit=queue_limit)

    return {
        'notification_list': notification_list,
        'queue_limit': queue_limit,
    }

register.inclusion_tag('subscription/examples/yourlabs/widget.html')(subscription_yourlabs_widget)
