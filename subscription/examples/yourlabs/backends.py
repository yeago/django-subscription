import datetime
import time

from django.utils import simplejson
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import trans_real

from redis import Redis
from subscription.models import Subscription

from settings import *
from exceptions import *

class BaseBackend(object):
    def emit(self, text, subscribers_of=None, dont_send_to=None, queue=None,
             send_only_to=None, actor=None, context=None, **kwargs):

        if context is None:
            context = {}

        if send_only_to and not subscribers_of:
            for recipient in send_only_to:
                self.user_emit(recipient,
                    self.user_render(actor, text, recipient, context, kwargs),
                    context, kwargs, queue)

            return

        self.content_type = ContentType.objects.get_for_model(subscribers_of)
        subscription_kwargs = {'content_type': self.content_type, 'object_id': subscribers_of.pk}
        if send_only_to:
            subscription_kwargs.update({'user__in': send_only_to})

        for i in Subscription.objects.filter(**subscription_kwargs):
            if i.user in (dont_send_to or []):
                continue

            if send_only_to and i.user not in send_only_to:
                continue

            user_text = self.user_render(actor, text, i.user, context, kwargs)
            self.user_emit(i.user, user_text, context, kwargs, queue)

    def user_render(self, actor, text, user, context, kwargs):
        context = self.process_user_context(actor, text, user, context, kwargs)
        t = self.get_user_translation(user)
        if t:
            text = t.gettext(text) % context
        else:
            text = text % context
        return text

    def user_emit(self, user, text, context, kwargs=None,
                  queue='default', state=NOTIFICATION_STATES[0]):
        raise NotImplementedError("Override this!")

    def process_user_context(self, actor, text, user, context, kwargs):
        """
        Implement your own context processor here, it's used by user_render
        """
        return context

class TranslationBackend(object):
    def get_user_language_code(self, user):
        """
        Override to get the language from the user's profile if you want.
        """
        return LANGUAGE_CODE

    def get_user_translation(self, user):
        """
        Convenience method which you probably do not want to override
        """
        if USE_I18N:
            return trans_real.translation(self.get_user_language_code(user))
        else:
            return None

class PinaxBackend(object):
    """
    Implementation of get_user_language code for pinax.apps.account
    """
    def get_user_language_code(self, user):
        account = user.account_set.all()[0]
        return account.language

class HtmlBackend(object):
    """
    HTML implementation of 'actor' rendering.
    """
    def process_user_context(self, actor, text, user, context, kwargs):
        """
        If 'actor' is not already in context:
        - if actor is the user:
            - if translation: translated 'yo'
            - else: just 'yo'
        - else: a link to the actor using actor.get_absolute_url
        """
        if 'actor' not in context.keys():
            t = self.get_user_translation(user)
            if user == actor:
                if hasattr(self, 'actor_display_self'):
                    context['actor'] = self.actor_display_self

                if t:
                    context['actor'] = t.gettext('Yo')
                else:
                    context['actor'] = 'Yo'
            else:
                if hasattr(self, 'actor_display_other'):
                    context['actor'] = self.actor_display_other
                else:
                    context['actor'] = '<a href="%s">%s</a>' % (
                        actor.get_absolute_url(),
                        actor.username,
                    )

        return context

class RedisBackend(object):
    def __init__(self, prefix='subscription'):
        self.prefix = prefix

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            self._redis = Redis()
        return self._redis

    def get_key(self, user, state, queue='default'):
        if hasattr(user, 'pk'):
            user = user.pk

        return '%s::%s::%s::%s' % (
            self.prefix,
            user,
            state, 
            queue,
        )

    def get_timestamps_key(self, user, queue='default'):
        if hasattr(user, 'pk'):
            user = user.pk

        return '%s::timestamps::%s::%s' % (self.prefix, user, queue)

    def push_state(self, user, 
        state=NOTIFICATION_STATES[0], queue=NOTIFICATION_QUEUES[0]):
        """
        Upgrade the state of a user's notification. For example, if 
        'undelivered' is above 'unacknowledged', then pushing all
        notifications from 'undelivered' to 'unacknowledged'::

            backend.push_state(user, 'undelivered')

        By default, states will be a list containing only the first state in
        settings.SUBSCRIPTION_NOTIFICATION_STATES.

        Note that this function is not totally safe. If the server 
        crashes between the copy and the delete then duplicate notifications
        will result.
        """
        next_state_key = NOTIFICATION_STATES.index(state) + 1

        if next_state_key + 1 > len(NOTIFICATION_STATES):
            raise CannotPushLastState(state, NOTIFICATION_STATES)
        
        next_state = NOTIFICATION_STATES[next_state_key]

        notifications = self.redis.lrange(
            self.get_key(user, state, queue), 0, -1)

        for notification in notifications:
            self.redis.lpush(
                self.get_key(user, next_state, queue), notification)
            self.redis.lrem(self.get_key(user, state, queue), notification)

    def get_last_notifications(self, user, queues=NOTIFICATION_QUEUES, 
        queue_limit=-1, states=[NOTIFICATION_STATES[0]], minimal=False, 
        reverse=False, push=[NOTIFICATION_STATES[0]]):

        if queue_limit > 0:
            redis_queue_limit = queue_limit - 1
        else:
            redis_queue_limit = queue_limit

        result = {}
        for queue in queues:
            for state in states:
                if queue_limit > 0 and queue in result.keys():
                    if len(result[queue]['notifications']) >= queue_limit:
                        # enought for this queue
                        break

                serialized_notifications = self.redis.lrange(
                    self.get_key(user, state, queue), 0, redis_queue_limit)

                if queue not in result.keys():
                    result[queue] = {}
                    result[queue]['notifications'] = []

                for serialized_notification in serialized_notifications:
                    notification = self.unserialize(serialized_notification, minimal)
                    notification['initial_state'] = state
                    result[queue]['notifications'].append(notification)

                    if queue_limit > 0:
                        if len(result[queue]['notifications']) >= queue_limit:
                            # enought for this queue
                            break

            if reverse:
                result[queue]['notifications'].reverse()

        for queue in queues:
            result[queue]['counts'] = {
                'total': 0,
            }

            for s in NOTIFICATION_STATES:
                length = self.redis.llen(self.get_key(user, s, queue))
                result[queue]['counts'][s] = length
                result[queue]['counts']['total'] += length

            if push:
                for state in push:
                    self.push_state(user, state, queue)

        return result

    def get_all_notifications(self, user, states=NOTIFICATION_STATES, 
        queues=NOTIFICATION_QUEUES, order_by='timestamp', 
        push=[NOTIFICATION_STATES[0], NOTIFICATION_STATES[1]]):

        result = []
        for state in states:
            for queue in queues:
                serialized_notifications = self.redis.lrange(self.get_key(user, state, queue), 0, -1)
                for notification in serialized_notifications:
                    notification = self.unserialize(notification)
                    notification['initial_state'] = state
                    notification['queue'] = queue
                    result.append(notification)

        if order_by:
            result = sorted(result, key=lambda x: x[order_by])
        
        if push:
            for state in push:
                for queue in queues:
                    self.push_state(user, state, queue)

        return result
    
    def user_emit(self, user, text, context=None, kwargs=None, 
                  queue='default', state=NOTIFICATION_STATES[0]):
        context = context or {}

        if 'timestamp' not in kwargs:
            timestamp = time.mktime(datetime.datetime.now().timetuple())
        else:
            timestamp = kwargs['timestamp']

        timestamps = self.redis.lrange(
            self.get_timestamps_key(user, queue), 0, -1)

        while str(timestamp) in timestamps:
            timestamp += 1

        timestamp = int(timestamp)

        kwargs['timestamp'] = timestamp
        notification = self.serialize(user, text, context, kwargs)

        self.redis.lpush(self.get_timestamps_key(user, queue), timestamp)
        self.redis.lpush(self.get_key(user, state, queue), notification)

    def serialize(self, user, text, context, kwargs):
        kwargs['text'] = text
        return simplejson.dumps(kwargs)

    def unserialize(self, data, minimal=False):
        data = simplejson.loads(data)
        if not minimal:
            if 'timestamp' in data.keys():
                data['datetime'] = datetime.datetime.fromtimestamp(
                    data['timestamp'])
        return data

class AppIntegrationBackend(object):
    def get_user_object_url(self, user, obj):
        return obj.get_absolute_url()

    def process_user_context(self, actor, text, user, context, kwargs):
        context = super(AppIntegrationBackend, self).process_user_context(
                        actor, text, user, context, kwargs)
        t = self.get_user_translation(user)
        l = self.get_user_language_code(user)

        target_html = '<a href="%(url)s">%(name)s</a>'
        target_context = {}

        if 'comment' in context.keys():
            content = context['comment'].content_object

            target_context['url'] = self.get_user_object_url(user, content)

            attr = 'name_%s' % l
            if hasattr(content, attr):
                target_context['name'] = getattr(content, attr)
            elif content.__class__.__name__ == 'Action':
                if content.actor == user:
                    target_context['name'] = t.gettext('your action')
                else:
                    target_context['name'] = t.gettext('%s\'s action') % actor.username
            elif content.__class__.__name__ == 'User':
                if content == user:
                    target_context['name'] = t.gettext('your status')
                else:
                    target_context['name'] = t.gettext('%s\'s status') % actor.username
            
        if 'message' in context.keys():
            target_context['url'] = context['message'].get_absolute_url()
            target_context['name'] = t.gettext('private message')

        context['target'] = target_html % target_context
        return context

class SiteBackend(AppIntegrationBackend, TranslationBackend, PinaxBackend, 
                  HtmlBackend, RedisBackend, BaseBackend):
    pass

try:
    # monkey patch localeurl support .. which we'll get rid of with django 1.4
    from localeurl.utils import locale_url, strip_path
    def user_object_localeurl(self, user, obj):
        l = self.get_user_language_code(user)
        url = locale_url(strip_path(obj.get_absolute_url())[1], l)
        return url
    AppIntegrationBackend.get_user_object_url = user_object_localeurl
except ImportError:
    pass
