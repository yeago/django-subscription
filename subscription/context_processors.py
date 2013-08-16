from .stream import user_stream

def get_actstream(request):
    if not request.user.is_authenticated():
        return {}
    """
    If we have 'undelivered' items, we deliver them to the unacknowledged list
    """
    return {'actstream': user_stream(request.user, clear_undelivered=True)}


