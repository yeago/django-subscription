from django.conf.urls.defaults import *

urlpatterns = patterns('subscription.examples.yourlabs.views',
    url(r'^dropdown/ajax/$', 'dropdown_ajax', {
        'dropdowns': ['chat', 'friends'],
        'states': ['undelivered', 'unacknowledged', 'acknowledged'],
        'push_states': {
            'undelivered': 'unacknowledged',
        },
        'counter_state': 'unacknowledged',
    }, 'subscription_dropdown_ajax'),
    url(r'^dropdown/open/$', 'dropdown_open', {
        'push_states': {
            'unacknowledged': 'acknowledged',
        },
    }, 'subscription_dropdown_open'),
    url(r'^$', 'dropdown_more', {
        'push_states': {
            'undelivered': 'acknowledged',
            'unacknowledged': 'acknowledged',
        }
    }, 'subscription_dropdown_more')
)
