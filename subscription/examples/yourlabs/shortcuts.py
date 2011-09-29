import datetime

from subscription.examples.yourlabs.notification import Lazy, Notification

def emit_lazy(*args, **kwargs):
    kwargs['lazy'] = True

    if len(args) == 0:
        cls = Notification
    else:
        cls = args[0]

    if getattr(cls, 'kwargs_factory', False):
        kwargs = cls.kwargs_factory(**kwargs)
    
    for key, value in kwargs.items():
        kwargs[key] = Lazy(value)

    if 'timestamp' not in kwargs.keys() and 'sent_at' not in kwargs.keys():
        kwargs['sent_at'] = datetime.datetime.now()

    notification = cls(**kwargs)

    notification.emit()
    return notification

def emit_static(*args, **kwargs):
    kwargs['lazy'] = False
 
    if len(args) == 0:
        cls = Notification
    else:
        cls = args[0]

    if 'timestamp' not in kwargs.keys() and 'sent_at' not in kwargs.keys():
        kwargs['sent_at'] = datetime.datetime.now()

    if getattr(cls, 'kwargs_factory', False):
        kwargs = cls.kwargs_factory(**kwargs)
    
    notification = cls(**kwargs)

    notification.emit()
    return notification
