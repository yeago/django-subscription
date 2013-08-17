# Adopted Spec Format

http://activitystrea.ms/head/json-activity.html

# Subscribing

    Subscription.objects.subscribe(user,content_object) # Subscribes a user

# Emitting

    Subscription.objects.emit("comment.create", comment_spec,
                             subscribers_of=comment_obj.content_object)

    
    Subscription.objects.emit("comment.create", comment_obj,
        subscribers_of=comment_obj.content_object, emitter_class=ModelEmitter)

The args/kwargs to emit() are more or less shuttled straight to the SUBSCRIPTION_BACKEND(s),
which is a dict in your settings.py like:

    SUBSCRIPTION_BACKENDS = {
      'email': 'myproject.subscription_backends.Email',
      'redis': 'myproject.subscription_backends.Redis',
    }

# Writing a backend

You can subclass subscription.backends.BaseBackend. Right now the options are:
 
* instance
* verb
* activity stream spec attrs (published, target, object, actor)
* subscribers_of - Gets the recipients from the Subscription model
* dont_send_to - Useful for supressing comment messages to their own author, for example
* send_only_to - Useful for other things I guess
* **kwargs - Passed onto your backend subclass in case you need more info
