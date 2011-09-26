from django import shortcuts
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.comments.signals import comment_was_posted

from subscription.models import Subscription
from subscription.examples.yourlabs import notifications

# deploy examples for a quick try
from subscription.examples.yourlabs.apps import comments
# auto subscribe users to objects they comment
comments.comment_was_posted.connect(comments.comments_subscription)

# now, four DEAD SIMPLE examples to choose from:
#
comments.comment_was_posted.connect(
    comments.comment_static_text_notification)
#comments.comment_was_posted.connect(
    #comments.comment_static_template_notification)
#comments.comment_was_posted.connect(
    #comments.comment_lazy_text_notification)
#comments.comment_was_posted.connect(
    #comments.comment_lazy_template_notification)

from subscription.examples.yourlabs.apps import auth
auth.signals.post_save.connect(auth.auto_subscribe_user_to_himself, sender=User)
auth.subscribe_existing_users_to_themselves()

def user_detail(request, username,
    template_name='auth/user_detail.html', extra_context=None):
    context = {
        'user': shortcuts.get_object_or_404(User, username=username)
    }
    context.update(extra_context or {})
    return shortcuts.render(request, template_name, context)
