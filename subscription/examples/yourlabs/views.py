import datetime

from django import shortcuts
from django import http
from django.utils import simplejson

import subscription

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
    result = shortcuts.render(request, template_name, context)

    # we rendered without problem, let's move undelivered to unacknowledged
    b.push_states(request.user)

    return result

def json(request, queue_limit=5):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    b = subscription.get_backends()['site']()
    notification_list = b.get_new_notifications(request.user, 
        queue_limit=queue_limit)

    result = http.HttpResponse(simplejson.dumps(notification_list))
    
    # we rendered without problem, let's move undelivered to unacknowledged
    b.push_states(request.user)

    return result
