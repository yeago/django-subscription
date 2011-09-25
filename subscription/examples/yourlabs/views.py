import datetime

from django import template
from django import shortcuts
from django import http
from django.utils import simplejson

import subscription
from subscription.examples.yourlabs.settings import *

def list(request,
    template_name='subscription/examples/yourlabs/list.html', 
    extra_context=None):

    b = subscription.get_backends()['redis']()

    notifications = []
    for queue in NOTIFICATION_QUEUES:
        for state in NOTIFICATION_STATES:
            notifications += b.get_notifications(request.user, state, queue)
            b.push_state(request.user, state, queue)
    
    notifications = sorted(notifications, key=lambda n: n.timestamp)

    context = {
        'notification_list': notifications,
        'today': datetime.date.today()
    }

    context.update(extra_context or {})
    return shortcuts.render(request, template_name, context)

def json(request, limit=15,
    template_name='subscription/examples/yourlabs/dropdown.html'):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    b = subscription.get_backends()['redis']()
    
    queues = {}
    for queue in NOTIFICATION_QUEUES:
        new = b.count_notifications(request.user, queue=queue)
        new += b.count_notifications(request.user, NOTIFICATION_STATES[1], 
            queue)

        queues[queue] = {
            'count': new,
        }

        if new:
            notifications = []
            for state in NOTIFICATION_STATES:
                notifications += b.get_notifications(request.user, state=state,
                    queue=queue, limit=limit-len(notifications))

            print notifications
            queues[queue]['dropdown'] = template.loader.render_to_string(
                template_name, {
                    'notifications': notifications,
                    'request': request,
                })
            
            b.push_state(request.user, queue=queue)
        
    return http.HttpResponse(simplejson.dumps(queues))

def push(request):
    queue = request.GET['queue']

    b = subscription.get_backends()['redis']()
    b.push_state(request.user, NOTIFICATION_STATES[1], queue)
    
    return http.HttpResponse('OK')
