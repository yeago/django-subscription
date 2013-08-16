import datetime
import json
from .client import get_cache_client
from .cluster import cluster_specs

CATEGORIES = ['undelivered', 'acknowledged', 'unacknowledged']

def clear_streams(user):
    conn = get_cache_client()
    for cat in CATEGORIES:
        conn.delete("actstream::%s::%s" % (user.pk, cat))


def render_stream(stream):
    stream_redux = []
    if not stream:
        return stream_redux
    """
    Things are gonna get gross here. Basically, I want to transition to the new
    system of consuming specs without destroying all the old messages.

    We can considered the old ones already rendered. The new ones we can consolidate.

    So far we've been going with (datetime, textblob) so we're gonna stick with that
    for the new ones, too
    """
    neostream, legacy_stream = [], []
    for item in stream:
        try:
            timestamp, text = json.loads(item)
            legacy_stream.append((datetime.datetime.fromtimestamp(timestamp), text))
        except ValueError:
            neostream.append(json.loads(item))
    stream_redux.extend(cluster_specs(neostream))
    stream_redux.extend(legacy_stream)
    stream_redux = sorted(stream_redux, key=lambda x: x[0], reverse=True)
    return stream_redux

def get_stream(category, user_id=None, conn=None, deserialize=True, limit=None, renderer=None):
    limit = limit or -1
    conn = conn or get_cache_client()
    if category not in CATEGORIES:
        raise NotImplementedError

    user_id = user_id or '*'
    redis_list = conn.lrange("actstream::%s::%s" % (user_id, category), 0, limit)
    if renderer:
        return renderer(redis_list)
    return redis_list

def user_stream(user, clear_undelivered=False, limit=None):
    conn = get_cache_client()
    if clear_undelivered:
        undelivered = get_stream('undelivered', user.pk, conn)
        if undelivered:
            for u in reversed(undelivered):  # Flip em around so recent is done last
                conn.lpush("actstream::%s::unacknowledged" % user.pk, u)
        conn.delete("actstream::%s::undelivered" % user.pk)
        conn.delete("actstream::%s::email-sent" % user.pk)
    return dict((i, get_stream(i, user.pk, conn, limit=limit, renderer=render_stream)) for i in CATEGORIES)
