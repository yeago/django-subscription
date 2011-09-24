from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import project_specific

admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^$', 'subscription_test_project.views.home', name='home'),
    url(r'^user/(?P<username>[a-z]+)/$', project_specific.user_detail, name='user_detail'),
    url(r'^subscriptions/', include('subscription.examples.yourlabs.urls')),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
