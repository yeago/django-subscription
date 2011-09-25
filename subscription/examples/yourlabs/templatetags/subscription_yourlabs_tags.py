from django import template

import subscription
from subscription.examples.yourlabs.settings import *

register = template.Library()

@register.inclusion_tag('subscription/examples/yourlabs/widget.html')
def yourlabs_notification_widget(request, limit=15):
    if not request.user.is_authenticated():
        return {}

    b = subscription.get_backends()['redis']()

    queues = {}
    for queue in NOTIFICATION_QUEUES:
        queues[queue] = {
            'notifications': [],
            'counts': {},
        }
        for state in reversed(NOTIFICATION_STATES):
            queues[queue]['notifications'] += b.get_notifications(request.user, 
                state, queue, limit=limit-len(queues[queue]['notifications']))
            queues[queue]['counts'][state] = b.count_notifications(
                request.user, state, queue)

    print queues['chat']['notifications']

    return {'queues': queues, 'request': request}

@register.simple_tag(takes_context=True)
def yourlabs_notification_render(context, notification, view):
    return notification.get_display(context['request'].user, view)
