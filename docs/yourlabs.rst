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

Concept
-------

The architecture is articulated over three main pieces:

Notfication classes
    A notification class encapsulates all the variables and methods that a
    notification needs from emission to rendering.

Backends
    A backend is a class that takes notifications and is responsible for
    delivering notification instances to users.

Subscription model
    A simple model that links a user with any other model using a generic
    foreign key. It keeps track of user subscriptions.

Notification classes
>>>>>>>>>>>>>>>>>>>>

This might be hard for some of you so first i'm going to vaguely describe the
class, than ask you to read the class source, then go into deeper details.

A notification class, is a type of notification. A notification instance, is an
actual notification.

(this section of the documentation will be finished later. I just spent 2 hours
and need to do some paid work for a while)

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

Then, install the redis module for example::

    pip install redis

Install subscription base
`````````````````````````

Add to `INSTALLED_APPS`: `subscription.examples.yourlabs`.

Start with the base subscription backend, which you will probably override
later::

    SUBSCRIPTION_BACKENDS = { 
        'site': 'subscription.examples.yourlabs.backends.RedisBackend'
    }

Urls
````

Add to your root urlconf (ie. `urls.py`) urlpatterns::

    urlpatterns = patterns('',
        # [snip your urls]
        url(r'^notifications/', include('subscription.examples.yourlabs.urls')),
    )

This will provide some urls. 

dropdown
    This is not a view name but you need to understand this naming. A dropdown
    is a javascript widget that displays the notifications from a queue. A
    dropdown is not a queue, a dropdown *has* a queue.

subscription_dropdown_ajax
    This view is called by javascript every X seconds because it returns the
    inner html for the javascript dropdown widgets as well as some meta data.
    By default, it pushes notifications from the state undelivered to
    unacknowledged.

subscription_dropdown_open
    Ths view is called by javascript when the user clicks to the dropdown. By
    default, it pushes notifications of state unacknowledged to acknowledged.

subscription_dropdown_more
    This is the view that displays all notifications of a single dropdown.
    Typically it is linked from the inner dropdown HTML as "see more" link.

subscription_list
    This view displays all notifications from all queues.

The configuration of these views is done in their url definition. Take a look
at yourlabs/urls.py and see how it is customizable.

In the default configuration, a notification can be part of one of the two
queues (other and friends) and have one of the three states (undelivered,
unacknowledged, acknowledged).

Static files
````````````

.. admonition:: Skip this step if you're already using the great
                `django.contrib.staticfiles` or `django-staticfiles`

Copy subscription/examples/yourlabs/static/subscription where your HTTP server
can find it.

Integration with other applications
```````````````````````````````````

This example also provides integrations with several apps, if they are
installed. This includes:

- django.contrib.comments
- django_messages
- django-actstream

In most case this is fine. Else you might want to un-register some signals.
Anyway, you might find useful the shortcut functions `emit_*` in that file.

New notifications on page rendering
```````````````````````````````````

In your base template, add::

    {% load subscription_yourlabs_tags %}

    {% subscription_yourlabs_dropdown request 'friends' 'undelivered,unacknowledged,acknowledged' 'undelivered,unacknowledged' 15 %}

This will display a notifiction widget for the request, of queue 'friends', of
states 'undelivered,unacknowledged,acknowledged' but will only count
notifications of state 'undelivered,unacknowledged'.

This will display the notification widget with 15 initial notifications (which
is the default).

That doesn't even require javascript.

Live notifications with javascript
``````````````````````````````````

To power the widget with live updates, load jquery your way and then this
script::

    {% load static from staticfiles %}
    <script type="text/javascript" src="{% static 'subscription/jquery-implementation.js' %}" />

Or, if using Pinax, which uses the old staticfiles app::

    <script type="text/javascript" src="{{ STATIC_URL }}subscription/jquery-implementation.js" />

Then, instanciate the Subscription singleton::

    <script type="text/javascript">
        $(document).ready(function() {
            Subscription.factory('{% url subscription_json %}', '{% url subscription_push %}');
        });
    </script>

This will instanciate Subscription into Subscription.singleton. You can
override any method or option the same way. For example::

    <script type="text/javascript">
        $(document).ready(function() {
            Subscription.factory('{% url subscription_json %}', {
                'delay': 1000, /* update every second */
            });
        });
    </script>
