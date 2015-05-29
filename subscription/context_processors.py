from .stream import user_stream


def get_actstream(request):
    if not request.user.is_authenticated():
        return {}
    """
    If we have 'undelivered' items, we deliver them to the unacknowledged list
    """
    stream = user_stream(request.user)
    last_ack = request.user.get_profile().get_stream_acknowledged()

    if last_ack:
        unacknowledged = [item for item in stream if item[0] > last_ack]
    else:
        unacknowledged = stream

    return {'actstream': stream,
            'actstream_unacknowledged': unacknowledged}
