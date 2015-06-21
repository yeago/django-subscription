# Adopted Spec Format

http://activitystrea.ms/head/json-activity.html

# Subscribing

    Subscription.objects.subscribe(user, content_object) # Subscribes a user

# Emitting

## Just one person, but not if its the author of the comment

    Subscription.objects.to(comment_obj.content_object.user).not_to(comment_obj.user).emit("comment.create", comment_spec)
   
## All subscribers of the content objects except the author of the comment
 
    Subscription.objects.of(comment_obj).not_to(comment_obj.user).emit(
        "comment.create", comment_obj,
        emitter_class=ModelEmitter)

# Settings

The args/kwargs to emit() are more or less shuttled straight to the SUBSCRIPTION_BACKEND(s),
which is a dict in your settings.py like:

    SUBSCRIPTION_BACKENDS = {
      'email': 'myproject.subscription_backends.Email',
      'redis': 'myproject.subscription_backends.Redis',
    }

    SUBSCRIPTION_ACTSTREAM_PROPERTIES = [
       'contentOwner'
    ]
    # Use this if you wanna say fuckit to the 'official' activitystream properties


# Writing a backend

You can subclass subscription.backends.BaseBackend. Right now the options are:

SomeBackend.emit(recipient, 'some.verb', **activity_stream_spec_plus_whatever)

* recipient (auth.User) 
* verb
* activity stream spec attrs (published, target, object, actor)
* **kwargs - Passed onto your backend subclass in case you need more info
