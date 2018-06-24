from django.conf.urls import url
from subscription import views

urlpatterns = [
   url(r'^$', views.SubscriptionView.as_view(), name="subscriptions"),
   url(r'^notifications/ping/$', views.notifications_ping, name="notifications_ping"),
   url('unsubscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', views.unsubscribe, name="subscription_unsubscribe"),
   url('subscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', views.subscribe, name="subscription_subscribe"),
]
