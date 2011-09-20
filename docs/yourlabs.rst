subscription.examples.yourlabs
==============================

What this is about
------------------

Yourlabs example is a demonstration of what a cool reusable app that just adds
blazing fast facebook-like notifications to your project with minimal hassle.

I am `is_null`, a freelancer idling on `irc.freenode.net` 24/7 for years.
In an infinite quest for karma, and maybe because the anarchist in me loves the
idea that any worker can share tools without real notion of property, I'd love
to help so you can just send me private messages if you need support.

Running tests
-------------

The fastest way to run tests is to enter subscription_test_project and run
`./manage.py test subscription`. This will avoid that your actual project be
used as it may contain many apps and fixtures which would make running tests
much slower.

Installation
------------

Install Redis
`````````````

This example needs redis. Redis is probably available in your distro's package
manager. And fear not: it comes at the price of 0.42M in my distro (Arch
Linux). So that's really an affordable dependency. Then, you should start it as
you start any daemons in your distro. For example, `/etc/rc.d/redis start` in
my distro. Don't forget to add it to server start if you wish to keep it! This
is done by adding `redis` to the DAEMONS array of `/etc/rc.conf` in my distro.

Then, install the redis-py module for example::

    pip install redis-py

Install subscription base
`````````````````````````

.. admonition:: Note that `yourlabs.setup` does all that for you, so if you're
                using it to emove the boilerplate from settings then you can 
                skip this step until you want more customization.

If you've put this in a file called `subscription_backends.py` in your project
root, then this setting would work::

    SUBSCRIPTION_BACKENDS = { 
        'site': 'subscription.examples.yourlabs.backends.SiteBackend'
    }

If you want to use multiple queues like facebook, then also add this setting
which will serve as reference for this documentation::

    SUBSCRIPTION_NOTIFICATION_QUEUES = [
        'chat',
        'friends',
    ]

Note that you don't have to declare `SUBSCRIPTION_NOTIFICATION_QUEUES` in order
to use multiple queues. It *only* serves as default for methods like `push_states`.

AcknowledgeMiddleware
`````````````````````

.. admonition:: Note that `yourlabs.setup` does all that for you, so if you're
                using it to emove the boilerplate from settings then you can 
                skip this step until you want more customization.

You can add the simple middleware that pushes notifications from
unacknowledged to acknowledged. Add to `MIDDLEWARE_CLASSES`::

    'subscription.examples.yourlabs.middleware.AcknowledgeMiddleware'

This will move notifications from unacknowledged to acknowledged using the
queue and timestamp from the URL. For example::

    /foo/?subscription_timestamp=12314311&subscription_queue=chat

Will move the notification with timestame `12314311` and queue `chat` from
unacknowledged to acknowledged.

Urls
````

Add to your root urlconf (ie. `urls.py`) urlpatterns::

    urlpatterns = patterns('',
        # [snip your urls]
        url(r'^notifications/', include('subscription.examples.yourlabs.urls')),
    )

This will provide two urls:

- `subscription_list`: a page that lists notifications by day
- `subscription_json`: returns 10 new notifications as json, and counts

If you want to get a different number of notifications as json, just override
the url, for example::

    urlpatterns = patterns('',
        # [snip your urls]
        url(r'^notifications/', 
            include('subscription.examples.yourlabs.urls')),
        url(r'^notifications/json/$', 
            'subscription.examples.yourlabs.views.json', 
            {'queue_limit': 30}, name='subscription_json'),
    )

Static files
````````````

.. admonition:: Skip this step if you're already using the great
                `django.contrib.staticfiles`

Copy subscription/examples/yourlabs/static/subscription where your HTTP server
can find it.

Integration with other applications
```````````````````````````````````

.. admonition:: Skip this step if you don't want to use multiple queues.

This example also provides integrations with several apps, if they are
installed. This includes:

- django.contrib.comments
- django_messages
- django-actstream

In most case this is fine. Just add `subscription.examples.yourlabs` to
INSTALLED_APPS. This will cause django to run
`subscription.examples.yourlabs.models` which contains all the boilerplate
code that you might not want to re-invent.

Templates
`````````

.. admonition:: Skip this step if you've completed the above step.

If you just want templates, but no integration with other applications, then
add the path of `subscription/examples/yourlabs/templates` to
`settings.TEMPLATE_DIRS`.

Customize the backend
---------------------

Create such a backend::

    from subscription.examples.yourlabs import backends

    class SiteBackend(backends.TranslationBackend, backends.PinaxBackend, 
                      backends.HtmlBackend, backends.RedisBackend, 
                      backends.BaseBackend):
        pass

Obviously, you should remove `backends.TranslationBackend` if you don't need
translations. Also, you should remove `backends.PinaxBackend` if you're not
using pinax.apps.account.

Note that the first method you will want to override is probably
`process_user_context()`. It allows you to do all common context processing
before rendering notification texts.

If you've put this in a file called `subscription_backends.py` in your project
root, then this setting would work::

    SUBSCRIPTION_BACKENDS = {
        'site': 'subscription_backends.SiteBackend',
    }

Workflow
--------

Notify that james follows you, where `YOU` is your actual
`django.contrib.auth.models.User` instance::

    from subscription.models import Subscription

    self.b.user_emit(
        YOU,
        'james follows you', 
        {}, 
        {
            'actor_pk': 2,
            'timestamp': 1,
        },
        'friends'
    )

When `YOU` connect, the base template should render the initial notifications
list in the notifications widget like at the top left corner of facebook. These
notifications should be retrieved with::

    result = self.b.get_new_notifications(self.u, queue_limit=5)

The low level workflow is tested in `subscription/examples/yourlabs/tests.py`,
method `test_facebook_story`.
