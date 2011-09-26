from django.conf.urls.defaults import *

urlpatterns = patterns('subscription.examples.yourlabs.views',
    url(r'^dropdown/ajax/$', 'dropdown_ajax', {
        'dropdowns': ['chat', 'friends'],
        'states': ['undelivered', 'unacknowledged', 'acknowledged'],
        'counter_state': 'undelivered',
        'push_states': {
            'undelivered': 'unacknowledged',
        },
    }, 'subscription_dropdown_ajax'),
    url(r'^dropdown/open/$', 'dropdown_open', {
        'push_states': {
            'unacknowledged': 'acknowledged',
        },
    }, 'subscription_dropdown_open'),
    url(r'^subscription/$', 'list', {
        'push_states': {
            'undelivered': 'acknowledged',
            'unacknowledged': 'acknowledged',
        }
    }, 'subscription_list')
)
