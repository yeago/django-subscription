.. django-subscription documentation master file, created by
   sphinx-quickstart on Thu Sep 15 14:57:20 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-subscription's documentation!
===============================================

Contents:

.. toctree::
   :maxdepth: 2

Installation
------------

Install redis-py::

    pip install redis

Create a file 'subscription_backends.py' with this code::

    import time 
    import datetime 
    
    from django.utils import simplejson 
    from redis import Redis 
    from subscription import backends 
    
    class RedisBackend(backends.BaseBackend): 
        def user_emit(self,user,text,**kwargs): 
            conn = Redis() 
            item = simplejson.dumps((time.mktime(datetime.datetime.now().timetuple()),text)) 
            conn.lpush("actstream::%s::undelivered" % user.pk,item) 

And add to your project and to settings.py::

    SUBSCRIPTION_BACKENDS = { 
        'redis': 'subscription_backends.RedisBackend',
    }

Integration of comments
-----------------------

This example demonstrates how to subscribe users to the objects they comment
automatically::

    from django.contrib.comments.models import Comment
    from django.contrib.comments.signals import comment_was_posted

    from subscription.models import Subscription

    def auto_subscribe(sender, **kwargs):
        comment = kwargs.pop('comment')
        Subscription.objects.subscribe(comment.user,comment.content_object)
    comment_was_posted.connect(auto_subscribe, sender=Comment)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

