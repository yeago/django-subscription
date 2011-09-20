import datetime

from django.utils import unittest

from subscription.examples.yourlabs import backends

class RedisBackendTest(unittest.TestCase):
    def setUp(self):
        b = backends.RedisBackend(prefix='test_subscription')
        self.assertEqual(b.get_key(1, 'a', 'b'), 'test_subscription::1::a::b',
                         'get_key is broken, cannot run tests safely')
        self.b = b

        class UserMock(object):
            def __init__(self, pk):
                self.pk = pk
        self.u = UserMock(1)

        self.maxDiff = None

    def tearDown(self):
        for key in self.b.redis.keys('test*'):
            self.b.redis.delete(key)

    def test_serialization(self):
        fixture = [self.u, 'foo', {'a': 'hello'}, {'important': 'foo'}]
        value = self.b.serialize(*fixture)
        actual = self.b.unserialize(value)
        self.assertEqual([u'text', u'important'], actual.keys())
        
        actual = self.b.unserialize(value, True)
        self.assertEqual([u'text', u'important'], actual.keys())

        fixture[3]['timestamp'] = 1316504374
        expected = {
            u'timestamp': 1316504374.0, 
            u'important': u'foo', 
            u'text': u'foo',
            u'datetime': datetime.datetime(2011, 9, 20, 2, 39, 34),
        }
        value = self.b.serialize(*fixture)
        actual = self.b.unserialize(value)
        self.assertEqual(expected, actual)

    def test_user_emit(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y'})
        result = self.b.redis.lrange(
            self.b.get_key(1, 'undelivered', 'default'), 0, -1)
        self.assertEqual(1, len(result))

    def test_push_states(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y'})
        self.b.push_states(self.u)
        
        result = self.b.redis.llen(
            self.b.get_key(1, 'undelivered', 'default'))
        self.assertEqual(0, result)

        result = self.b.redis.llen(
            self.b.get_key(1, 'unacknowledged', 'default'))
        self.assertEqual(1, result)
    
    def test_push_states_with_noise(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y'})
        self.b.push_states(self.u)
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y'})

        result = self.b.redis.llen(
            self.b.get_key(1, 'undelivered', 'default'))
        self.assertEqual(1, result)

        result = self.b.redis.llen(
            self.b.get_key(1, 'unacknowledged', 'default'))
        self.assertEqual(1, result)

    def test_get_last_notifications(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y', 'timestamp': 5})
        result = self.b.get_last_notifications(self.u)
        
        expected = {
            'default': {
                u'notifications': [
                    {
                        u'x': u'y', 
                        u'timestamp': 5, 
                        u'text': u'foo',
                        u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 5),
                    },
                ], 
                u'counts': {
                    'undelivered': 1, 
                    u'total': 1, 
                    'acknowledged': 0, 
                    'unacknowledged': 0
                }
            }
        }

        self.assertEqual(expected, result)
    
    def test_get_last_notifications_with_noise(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})
        self.b.push_states(self.u)
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 3})
        result = self.b.get_last_notifications(self.u)
        
        expected = {
            'default': {
                'notifications': [
                    {
                        u'x': u'y', 
                        u'timestamp': 3, 
                        u'text': u'foo',
                        u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 3)
                    },
                ], 
                'counts': {
                    'undelivered': 1, 
                    u'total': 2, 
                    'acknowledged': 0, 
                    'unacknowledged': 1
                }
            }
        }

        self.assertEqual(expected, result)
    
    def test_get_all_notifications(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})
        self.b.push_states(self.u)
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 3})

        expected = [
            {
                u'x': u'y', 
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 3), 
                u'timestamp': 3, 
                u'text': u'foo',
                u'queue': 'default',
                u'state': 'undelivered',
            }, 
            {
                u'x': u'y', 
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1), 
                u'timestamp': 1, 
                u'text': u'foo',
                u'queue': 'default',
                u'state': 'unacknowledged',
            }
        ]
        result = self.b.get_all_notifications(self.u)

        self.assertEqual(expected, result)
    
    def test_push_notification(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})
        # push to delivered
        self.b.push_states(self.u)

        # should push to acknowledged!
        self.b.push_notification(self.u, 1)

        expected = [
            {
                u'timestamp': 1, 
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1), 
                u'queue': 'default', 
                u'state': 'acknowledged', 
                u'text': u'foo', 
                u'x': u'y',
            }
        ]
        result = self.b.get_all_notifications(self.u)
        self.assertEqual(expected, result)
    
    def test_user_emit_uniques_timestamps(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})
        self.b.user_emit(self.u, 'bar', {}, {'x': 'y','timestamp': 1})

        expected = [
            {
                u'timestamp': 2, 
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 2),
                u'queue': 'default',
                u'state': 'undelivered',
                u'text': u'bar',
                u'x': u'y'
            },
            {
                u'timestamp': 1,
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                u'queue': 'default',
                u'state': 'undelivered',
                u'text': u'foo',
                u'x': u'y'
            },
        ]

        result = self.b.get_all_notifications(self.u)
        self.assertEqual(expected, result)

    def test_push_notification_with_noise(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})
        # push to delivered
        self.b.push_states(self.u)
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y','timestamp': 1})

        # should push to acknowledged!
        self.b.push_notification(self.u, 1)

        expected = [
            {
                u'timestamp': 3, 
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 3),
                u'queue': 'default',
                u'state': 'undelivered',
                u'text': u'foo',
                u'x': u'y'
            },
            {
                u'timestamp': 2,
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 2),
                u'queue': 'default',
                u'state': 'unacknowledged',
                u'text': u'foo',
                u'x': u'y'
            },
            {
                u'timestamp': 1,
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                u'queue': 'default',
                u'state': 'acknowledged',
                u'text': u'foo',
                u'x': u'y'
            }
        ]

        result = self.b.get_all_notifications(self.u)
        self.assertEqual(expected, result)
    
    def test_facebook_story(self):
        self.b.user_emit(self.u, 'noise', {}, {'x': 'y','timestamp': 1}, 'friends')
        self.b.user_emit(self.u, 'noise', {}, {'x': 'y','timestamp': 1}, 'friends')
        self.b.user_emit(self.u, 'noise', {}, {'x': 'y','timestamp': 1}, 'friends')
        self.b.user_emit(self.u, 'noise', {}, {'x': 'y','timestamp': 1}, 'friends')
        self.b.user_emit(self.u, 'noise', {}, {'x': 'y','timestamp': 1}, 'friends')
        self.b.user_emit(self.u, 'noise', {}, {'x': 'y','timestamp': 1}, 'friends')
        self.b.user_emit(
            self.u, 
            'james follows you', 
            {}, 
            {
                'actor_pk': 2,
                'timestamp': 1,
            },
            'friends'
        )

        # first event: page rendering for self.u.  the page should render the
        # initial notifications widget in our test case, only 1 of them, but
        # with total count for each queue. So if we show 1, and that the count
        # shows more, then we will deliver the other new notifications in a
        # "see X new notifications" link. 
        # Also note, here we specify the queues manually but it would default
        # on setting SUBSCRIPTION_NOTIFICATION_QUEUES
        result = self.b.get_last_notifications(self.u, 
            queues=['friends', 'chat'], queue_limit=1)

        # so we should push those from the first state to the next state
        self.b.push_states(self.u, queues=['friends', 'chat'])

        expected = {
            'chat': {
                u'counts': {
                    'acknowledged': 0,
                      u'total': 0,
                      'unacknowledged': 0,
                      'undelivered': 0
                },
                u'notifications': []
            },
            'friends': {
                u'counts': {
                    'acknowledged': 0,
                     u'total': 7,
                     'unacknowledged': 0,
                     'undelivered': 7
                },
                u'notifications': [
                    {
                        u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 7),
                        u'actor_pk': 2,
                        u'text': u'james follows you',
                        u'timestamp': 7
                    },
                ]
            }
        }
        self.assertEqual(expected, result)

        # james is connected as well. He sends a message to our user.
        self.b.user_emit(
            self.u, 
            'james sent a message', 
            {
                # you want to copy this to kwargs for live page
                # comments update ... this can be done by overloading
                # serialize()
                'message': 'hi bro!',
            },
            {
                'actor_pk': 2,
                'timestamp': 1,
            },
            'chat'
        )

        # Our user's javascript should poll for new notifications as such
        # (except for the queues argument again)
        result = self.b.get_last_notifications(self.u, 
            queues=['friends', 'chat'])
        
        # the javascript will display those so we should push those from the
        # first state to the next state
        self.b.push_states(self.u, queues=['friends', 'chat'])

        expected = {
            'chat': {
                u'counts': {
                    'acknowledged': 0,
                     u'total': 1,
                     'unacknowledged': 0,
                     'undelivered': 1
                },
                u'notifications': [
                    {
                        u'actor_pk': 2,
                        u'text': u'james sent a message',
                        u'timestamp': 1,
                        u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                    }
                ]
            },
            'friends': {
                u'counts': {
                    'acknowledged': 0,
                    u'total': 7,
                    'unacknowledged': 7,
                    'undelivered': 0
                },
                u'notifications': []
            }
        }

        self.assertEqual(expected, result)
       
        # finnaly, our user will click on the message notification to reply so
        # we should push it to the next state
        self.b.push_notification(self.u, 1, 'chat')

        # let's see if that worked while testing that the /notifications page
        # has all the right data
        result = self.b.get_all_notifications(self.u, 
            queues=['chat', 'friends'])
        expected = [
            {
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'noise',
                u'timestamp': 1,
                u'x': u'y'
            },
            {
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 2),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'noise',
                u'timestamp': 2,
                u'x': u'y'
            },
            {
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 3),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'noise',
                u'timestamp': 3,
                u'x': u'y'
            },
            {
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 4),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'noise',
                u'timestamp': 4,
                u'x': u'y'
            },
            {
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 5),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'noise',
                u'timestamp': 5,
                u'x': u'y'
            },
            {
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 6),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'noise',
                u'timestamp': 6,
                u'x': u'y'
            },
            {
                u'actor_pk': 2,
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 7),
                u'queue': 'friends',
                u'state': 'unacknowledged',
                u'text': u'james follows you',
                u'timestamp': 7
            },
            {
                u'actor_pk': 2,
                u'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                u'queue': 'chat',
                u'state': 'acknowledged',
                u'text': u'james sent a message',
                u'timestamp': 1
            }
        ]

        self.assertEqual(expected, result)
