import datetime

from django import template
from django import shortcuts
from django import http
from django.utils import simplejson

import subscription
from subscription.examples.yourlabs.settings import *

def list(request, rename=None,
    template_name='subscription/examples/yourlabs/list.html', 
    extra_context=None):
    
    if rename is None:
        rename = {}

    queues = request.GET.get('queues', 'default').split(';')

    b = subscription.get_backends()['redis']()

    notifications = []
    for queue in queues:
        notifications += b.get_notifications(queue)

        for pattern, replacement in rename:
            if pattern in queue:
                b.move_queue(queue, queue.replace(pattern, replacement))
    
    notifications = sorted(notifications, key=lambda n: n.timestamp)

    context = {
        'notification_list': notifications,
        'today': datetime.date.today()
    }

    context.update(extra_context or {})
    return shortcuts.render(request, template_name, context)

def dropdown_ajax(request, dropdowns=None, states=None, counter_states=None, 
    rename=None, limit=15, 
    template_name='subscription/examples/yourlabs/dropdown.html'):

    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    context = {}
    for dropdown in dropdowns:
        context[dropdown] = {
            'counter': 0,
        }
        notifications = []

        for state in counter_states:
            q = 'dropdown=%s,user=%s,%s' % (dropdown, request.user.pk, state)
            context[dropdown]['counter'] += b.count_notifications(q)

        for state in states:
            q = 'dropdown=%s,user=%s,%s' % (dropdown, request.user.pk, state)
            notifications += b.get_notifications(queue=q, 
                limit=limit-len(notifications))

            for pattern, replacement in rename:
                if pattern in q:
                    b.move_queue(q, q.replace(pattern, replacement))

        context[dropdown]['html'] = template.loader.render_to_string(
        template_name, {
            'notifications': notifications,
            'request': request,
        })

    return http.HttpResponse(simplejson.dumps(context))

def dropdown_open(request, rename=None):
    dropdown = request.GET['dropdown']

    for pattern, replacement in rename:
        q = 'dropdown=%s,user=%s,%s' % (dropdown, request.user.pk, pattern)
        b.move_queue(q, q.replace(pattern, replacement))
    
    return http.HttpResponse('OK')
