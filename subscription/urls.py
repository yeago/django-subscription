from django.urls import re_path
from subscription import views

urlpatterns = [
   re_path(r'^$', views.SubscriptionView.as_view(), name="subscriptions"),
   re_path(r'^notifications/ping/$', views.notifications_ping, name="notifications_ping"),
   re_path('unsubscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', views.unsubscribe, name="subscription_unsubscribe"),
   re_path('subscribe/(?P<content_type>\d+)/(?P<object_id>\d+)/', views.subscribe, name="subscription_subscribe"),
]
