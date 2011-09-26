from django import template

import subscription
from subscription.examples.yourlabs.settings import *

register = template.Library()

@register.inclusion_tag('subscription/examples/yourlabs/dropdown.html')
def subscription_yourlabs_dropdown(request, dropdown, states, count, limit=15):
    if not request.user.is_authenticated():
        return {}

    b = subscription.get_backends()['storage']()

    notifications = []
    for state in states.split(','):
        q = 'dropdown=%s,user=%s,%s' % (dropdown, request.user.pk, state)
        notifications += b.get_notifications(q, limit-len(notifications))

    counter = 0
    for state in count.split(','):
        q = 'dropdown=%s,user=%s,%s' % (dropdown, request.user.pk, state)
        counter += b.count_notifications(q)
    
    return {
        'notifications': notifications,
        'counter': counter,
        'dropdown': dropdown,
        'request': request,
    }

@register.simple_tag(takes_context=True)
def yourlabs_notification_render(context, notification, view='html'):
    return notification.display(context['request'].user, view)
