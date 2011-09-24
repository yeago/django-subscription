from django import shortcuts
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.comments.signals import comment_was_posted

from subscription.models import Subscription
from subscription.examples.yourlabs import notifications

# load examples
from subscription.examples.yourlabs.apps import comments as comments_example
from subscription.examples.yourlabs.apps import auth as auth_example

def user_detail(request, username,
    template_name='auth/user_detail.html', extra_context=None):
    context = {
        'user': shortcuts.get_object_or_404(User, username=username)
    }
    context.update(extra_context or {})
    return shortcuts.render(request, template_name, context)
