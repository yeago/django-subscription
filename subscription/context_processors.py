import time
from .stream import user_stream


def get_actstream(request):
    if not request.user.is_authenticated():
        return {}
    """
    If we have 'undelivered' items, we deliver them to the unacknowledged list
    """
    stream = user_stream(request.user)

    last_ack = request.user.get_profile().get_stream_acknowledged()
    unacknowledged = user_stream(request.user, newer_than=last_ack)

    return {'actstream': stream,
            'actstream_unacknowledged': unacknowledged}
