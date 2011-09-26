import datetime

from subscription.examples.yourlabs.notification import Lazy

def emit_lazy(cls, **kwargs):
    kwargs['lazy'] = True

    if getattr(cls, 'kwargs_factory', False):
        kwargs = cls.kwargs_factory(**kwargs)
    
    for key, value in kwargs.items():
        kwargs[key] = Lazy(value)

    notification = cls(**kwargs)

    if not getattr(notification, 'sent_at', False):
        notification.sent_at = datetime.datetime.now()

    notification.emit()
    return notification

def emit_static(cls, **kwargs):
    kwargs['lazy'] = False
    
    if getattr(cls, 'kwargs_factory', False):
        kwargs = cls.kwargs_factory(**kwargs)
    
    notification = cls(**kwargs)

    if not getattr(notification, 'sent_at', False):
        notification.sent_at = datetime.datetime.now()

    notification.emit()
    return notification
