import datetime
from .stream import user_stream

def get_actstream(request):
    if not request.user.is_authenticated():
        return {}
    """
    If we have 'undelivered' items, we deliver them to the unacknowledged list
    """
    stream = user_stream(request.user)
    unacknowledged = None
    if stream:
        unacknowledged = request.user.get_profile(
            ).stream_pending_acknowledgements(stream[0][0])
    redux = []
    for item in stream:
        future = False
        if item[0] > datetime.datetime.now():
            future = True
        redux.append((item, future))
    return {'actstream': redux,
            'actstream_unacknowledged': unacknowledged}
