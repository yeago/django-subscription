import json
import time
from subscription import backends
from redis import Redis

class ActStream(backends.BaseBackend):
    def emit(self,user,text,**kwargs):
        conn = Redis() # Need your host settings
        item = json.dumps((time.mktime(datetime.datetime.now().timetuple()),text))
        conn.lpush("actstream::%s::undelivered" % user.pk,item)
