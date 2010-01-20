from django.conf.urls.defaults import *

urlpatterns = patterns('subscription.views',
   url('unsubscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', 'unsubscribe', name="subscription_unsubscribe"),
   url('subscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', 'subscribe', name="subscription_subscribe"),
)
