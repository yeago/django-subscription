from django.db.models import signals

from django_messages.models import Message

def auto_message_notification(sender, **kwargs):
    if not kwargs.get('created', False):
        return
    emit_new_message(kwargs['instance'])
signals.post_save.connect(auto_message_notification, sender=Message)

def emit_new_message(message):
    Subscription.objects.emit(
        u'%(actor_display)s sent you a %(target)s',
        send_only_to=[message.recipient],
        context={
            'message': message,
            'actor': message.sender,
        },
        queue='chat',
    )
