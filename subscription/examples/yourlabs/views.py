import datetime

from django import shortcuts
from django import http
from django.utils import simplejson

import subscription
from subscription.examples.yourlabs.settings import *

def list(request,
    template_name='subscription/examples/yourlabs/list.html', 
    extra_context=None):

    b = subscription.get_backends()['site']()
    notification_list = b.get_all_notifications(request.user)

    context = {
        'notification_list': notification_list,
        'today': datetime.date.today()
    }

    context.update(extra_context or {})
    return shortcuts.render(request, template_name, context)

def json(request, queue_limit=15):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    b = subscription.get_backends()['site']()
    notification_list = b.get_last_notifications(request.user, 
        queue_limit=queue_limit, minimal=True, reverse=True)

    return http.HttpResponse(simplejson.dumps(notification_list))

def push(request):
    queue = request.GET['queue']

    b = subscription.get_backends()['site']()
    b.push_state(request.user, NOTIFICATION_STATES[1], queue)
    
    return http.HttpResponse('OK')
