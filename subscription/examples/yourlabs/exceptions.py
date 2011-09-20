class SubscriptionException(Exception):
    """
    Base exception for all exceptions that are raised by this example.
    """
    pass

class CannotPushLastState(SubscriptionException):
    def __init__(self, state, states):
        msg = 'Cannot push notifications of state %s because it is the last state of your states list %s' % (state, states)
        super(CannotPushLastState, self).__init__(msg)
