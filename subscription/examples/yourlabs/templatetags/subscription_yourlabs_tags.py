import datetime

from django import template
from django.utils.translation import ugettext, ungettext

import subscription
from subscription.examples.yourlabs.settings import *

register = template.Library()

@register.inclusion_tag('subscription/dropdown.html')
def subscription_yourlabs_dropdown(request, dropdown, states, count, limit=15):
    if not request.user.is_authenticated():
        return {}

    b = subscription.get_backends()['storage']()

    notifications = []
    queues = []
    for state in states.split(','):
        q = 'dropdown=%s,user=%s,%s' % (dropdown, request.user.pk, state)
        queues.append(q)
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
        'queues': queues,
    }

@register.simple_tag(takes_context=True)
def yourlabs_notification_render(context, notification, view='html'):
    return notification.display(context['request'].user, view)

# courtesy of http://djangosnippets.org/snippets/2275/
@register.filter(name='timesince_human')
def humanize_timesince(date):
    delta = datetime.datetime.now() - date

    num_years = delta.days / 365
    if (num_years > 0):
        return ungettext(u"%d year ago", u"%d years ago", num_years) % num_years

    num_weeks = delta.days / 7
    if (num_weeks > 0):
        return ungettext(u"%d week ago", u"%d weeks ago", num_weeks) % num_weeks

    if (delta.days > 0):
        return ungettext(u"%d day ago", u"%d days ago", delta.days) % delta.days

    num_hours = delta.seconds / 3600
    if (num_hours > 0):
        return ungettext(u"%d hour ago", u"%d hours ago", num_hours) % num_hours

    num_minutes = delta.seconds / 60
    if (num_minutes > 0):
        return ungettext(u"%d minute ago", u"%d minutes ago", num_minutes) % num_minutes

    return ungettext(u"%d second ago", u"%d seconds ago", delta.seconds) % delta.seconds
