import datetime
import json
from .client import get_cache_client
from .cluster import cluster_specs

UNDELIVERED = 'undelivered'
ACKNOWLEDGED = 'acknowledged'
UNACKNOWLEDGED = 'unacknowledged'

CATEGORIES = [UNDELIVERED, ACKNOWLEDGED, UNACKNOWLEDGED]

def clear_streams(user):
    conn = get_cache_client()
    for cat in CATEGORIES:
        conn.delete("actstream::%s::%s" % (user.pk, cat))


def render_stream(stream, newer_than=None):
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
            neostream.append(json.loads(item))
    if newer_than:
        neostream = [i for i in neostream if not i.get('published') or i['published'] > newer_than]
    stream_redux.extend(cluster_specs(neostream))
    stream_redux.extend(legacy_stream)
    stream_redux = sorted(stream_redux, key=lambda x: x[0], reverse=True)
    return stream_redux

def get_stream(category, user_id=None, conn=None, limit=None, renderer=None, newer_than=None):
    """
    * limit - The redis limit to apply to the list (maybe you only want the last 20)
    * newer_than - Epoch of the earliest messages you want.
    """
    limit = limit or -1
    conn = conn or get_cache_client()
    if category not in CATEGORIES:
        raise NotImplementedError

    user_id = user_id or '*'
    redis_list = conn.lrange("actstream::%s::%s" % (user_id, category), 0, limit)
    if renderer:
        return renderer(redis_list, newer_than=newer_than)
    return redis_list

def user_stream(user, clear_undelivered=False, limit_lambda=None, newer_than_lambda=None):
    """
    * limit_labmda - Cheesy as fuck hook to pass limit to a list
    * newer_than_lambda - Cheesy as fuck hook to pass newer_than to a list

    BACKSTORY -- You probably want to deliver all unacknowledged but you might not want
    the entire history of everything they've already seen.
    """
    conn = get_cache_client()
    if clear_undelivered:
        undelivered = get_stream(UNDELIVERED, user.pk, conn)
        if undelivered:
            for u in reversed(undelivered):  # Flip em around so recent is done last
                conn.lpush("actstream::%s::unacknowledged" % user.pk, u)
        conn.delete("actstream::%s::undelivered" % user.pk)
        conn.delete("actstream::%s::email-sent" % user.pk)
    groups = {}
    for CAT in CATEGORIES:
        newer_than, limit = None, None
        if newer_than_lambda:
            newer_than = newer_than_lambda(CAT)
        if limit_lambda:
            limit = limit_lambda(CAT)
        groups[CAT] = get_stream(CAT, user.pk, conn,
            limit=limit, newer_than=newer_than, renderer=render_stream)
    return groups
