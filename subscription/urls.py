try:
   from django.conf.urls.defaults import patterns, url  # Django 1.4
except ImportError:
   from django.conf.urls import patterns, url  # Django >= 1.6
from subscription.views import SubscriptionView

urlpatterns = patterns('subscription.views',
   url(r'^$', SubscriptionView.as_view(), name="subscriptions"),
   url(r'^notifications/ping/$', 'notifications_ping', name="notifications_ping"),
   url('unsubscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', 'unsubscribe', name="subscription_unsubscribe"),
   url('subscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', 'subscribe', name="subscription_subscribe"),
)
