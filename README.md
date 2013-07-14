# Adopted Spec Format

http://activitystrea.ms/head/json-activity.html

# Subscribing

    Subscription.objects.subscribe(user,content_object) # Subscribes a user

# Emitting

    Subscription.objects.emit("comment.create", comment_obj,
                             subscribers_of=comment_obj.content_object)

The args/kwargs to emit() are more or less shuttled straight to the SUBSCRIPTION_BACKEND(s),
which is a dict in your settings.py like:

    SUBSCRIPTION_BACKENDS = {
      'email': 'myproject.subscription_backends.Email',
      'redis': 'myproject.subscription_backends.Redis',
    }

# Writing a backend

You can subclass subscription.backends.BaseBackend. Right now the options are:
 
* instance
* verb
* subscribers_of - Gets the recipients from the Subscription model
* dont_send_to - Useful for supressing comment messages to their own author, for example
* send_only_to - Useful for other things I guess
* **kwargs - Passed onto your backend subclass in case you need more info
 
 
 
## Sample setup


    #backend.py
    from subscription import backends
    from .utils import Redis
    class ActStream(backends.BaseBackend):
        def emit(self, user, spec, **kwargs):
            conn = Redis()
            item = json.dumps((time.mktime(datetime.datetime.now().timetuple()), spec))
            conn.lpush("actstream::%s::undelivered" % user.pk,item)
    #retrieve.py
    def user_stream(user, clear_undelivered=False):
        def deserialize_stream(stream):
            stream_redux = []
            if not stream:
                return stream_redux
            for s in stream:
                s = json.loads(s)
                stream_redux.append((datetime.datetime.fromtimestamp(s[0]),s[1]))
            return stream_redux
        conn = Redis()
        if clear_undelivered:
            undelivered = conn.lrange("actstream::%s::undelivered" % user.pk,0,-1)
            if undelivered:
                for u in reversed(undelivered): # Flip em around so recent is done last
                    conn.lpush("actstream::%s::unacknowledged" % user.pk,u)
            conn.delete("actstream::%s::undelivered" % user.pk)
        groups = {}
        groups['acknowledged'] = deserialize_stream(conn.lrange("actstream::%s::acknowledged" % (user.pk),0,-1))
        groups['unacknowledged'] = deserialize_stream(conn.lrange("actstream::%s::unacknowledged" % (user.pk),0,-1))
        groups['undelivered'] = deserialize_stream(conn.lrange("actstream::%s::undelivered" % (user.pk),0,-1))
        return groups
        def deserialize_stream(redis_args):
            # Pull from redis, display however the heck you want.
