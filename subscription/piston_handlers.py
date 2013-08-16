try:
    from piston.handler import BaseHandler
except ImportError:
    """
    For many reasons you probably aren't using piston and
    I'm not either but here's the code anyhow.
    """
    class BaseHandler(object):
        pass

from django.utils.timesince import timesince
from .client import get_cache_client
from .stream import user_stream


class NotificationHandler(BaseHandler):
    allowed_methods = ['GET']
    def read(self,request):
        if not request.user.is_authenticated():
            # No fucking idea what rc is. Sorry! Fuck piston.
            # raise rc.FORBIDDEN
            raise Exception("Stop using piston or fix this?")
        return user_stream(request.user)


class NewNotificationHandler(NotificationHandler):
    """
    This served them any actions in their 'undelivered' redis list and dumps them into the
    'unacknowledged' list. The ping acknowledges them.
    """
    def read(self,request):
        actions = super(NewNotificationHandler,self).read(request)
        if not actions.get("undelivered"):
            return []

        conn = get_cache_client()
        with conn.pipeline() as pipe:
            [pipe.lpush("actstream::%s::unacknowledged" % request.user.pk,u) \
                for u in conn.lrange("actstream::%s::undelivered" % request.user.pk,0,-1)]
            pipe.execute()

        conn.delete("actstream::%s::undelivered" % request.user.pk)
        undelivered = []
        for u in actions.get("undelivered"):
            undelivered.append("%s &mdash; %s ago" % (u[1],timesince(u[0])))
        return undelivered
