def user_stream(user,clear_undelivered=False):
    conn = Redis()

    def deserialize_stream(stream):
        stream_redux = []
        for s in stream:
            s = json.loads(s)
            stream_redux.append((datetime.datetime.fromtimestamp(s[0]),s[1]))

        return stream_redux

    if clear_undelivered:
        undelivered = conn.lrange("actstream::%s::undelivered" % user.pk,0,-1)
        for u in undelivered:
            conn.lpush("actstream::%s::unacknowledged" % user.pk,u)

        conn.delete("actstream::%s::undelivered" % user.pk)

    groups = {}
    groups['acknowledged'] = deserialize_stream(conn.lrange("actstream::%s::acknowledged" % (user.pk),0,-1))
    groups['unacknowledged'] = deserialize_stream(conn.lrange("actstream::%s::unacknowledged" % (user.pk),0,-1))
    groups['undelivered'] = deserialize_stream(conn.lrange("actstream::%s::undelivered" % (user.pk),0,-1))
    return groups
