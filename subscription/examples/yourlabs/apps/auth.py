from django.db.models import signals
from django.contrib.auth.models import User

from subscription.models import Subscription

def auto_subscribe_user_to_himself(sender, **kwargs):
    user = kwargs.pop('instance')
    Subscription.objects.subscribe(user, user)

def subscribe_existing_users_to_themselves():
    for user in User.objects.all():
        Subscription.objects.subscribe(user, user)
