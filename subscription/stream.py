import datetime
import json
from .client import get_cache_client
from .cluster import cluster_specs

def clear_stream(user, conn=None):
    conn = conn or get_cache_client()
    conn.delete("actstream::%s" % (user.pk))


def render_stream(stream, newer_than=None, self=None):
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
            if newer_than and timestamp < newer_than:
                continue
            legacy_stream.append((datetime.datetime.fromtimestamp(timestamp), text))
        except ValueError:
            item = json.loads(item)
            neostream.append(item)
    if newer_than:
        neostream = [i for i in neostream if not i.get('published') or \
            datetime.datetime.fromtimestamp(i['published']) > newer_than]
    stream_redux.extend(cluster_specs(neostream))
    stream_redux.extend(legacy_stream)
    stream_redux = sorted(stream_redux, key=lambda x: x[0], reverse=True)
    return stream_redux

def get_stream(user_id, conn=None, limit=None, renderer=None, newer_than=None):
    """
    * limit - The redis limit to apply to the list (maybe you only want the last 20)
    * newer_than - Epoch of the earliest messages you want.
    """
    limit = limit or -1
    conn = conn or get_cache_client()
    user_id = user_id or '*'
    redis_list = conn.lrange("actstream::%s" % (user_id), 0, limit)
    if renderer:
        return renderer(redis_list, newer_than=newer_than, self=user_id)
    return redis_list

def user_stream(user, limit=None, newer_than=None):
    """
    * limit_labmda - Cheesy as fuck hook to pass limit to a list
    * newer_than - Stream items greater than this

    BACKSTORY -- You probably want to deliver all
    unacknowledged but you might not want
    the entire history of everything they've already seen.
    """
    conn = get_cache_client()
    return get_stream(user.pk, conn,
        limit=limit, newer_than=newer_than, renderer=render_stream)
