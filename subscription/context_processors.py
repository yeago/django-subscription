from .stream import user_stream
import time
import datetime

def newer_than_lambda(CAT):
    if CAT == 'acknowledged':
        return time.mktime((datetime.datetime.now() - datetime.timedelta(days=5)).timetuple())

def get_actstream(request):
    if not request.user.is_authenticated():
        return {}
    """
    If we have 'undelivered' items, we deliver them to the unacknowledged list
    """
    return {'actstream': user_stream(request.user, clear_undelivered=True, newer_than_lambda=newer_than_lambda)}
