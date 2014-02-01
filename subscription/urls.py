from django.conf.urls.defaults import patterns, url
from subscription.views import SubscriptionView

urlpatterns = patterns('subscription.views',
   url(r'^$', SubscriptionView.as_view(), name="subscriptions"),
   url(r'^actstream/ping/$', 'actstream_ping', name="actstream_ping"),
   url('unsubscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', 'unsubscribe', name="subscription_unsubscribe"),
   url('subscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', 'subscribe', name="subscription_subscribe"),
)
