import datetime

from pprint import pprint

from django.utils import unittest

from subscription.examples.yourlabs import backends

class BackendTestUtils(object):
    @classmethod
    def tearDownClass(cls):
        raise NotImplementedError('I should clean up test data!')

    def assertStateQueueLengthEqual(self, expected, state, queue='default'):
        raise NotImplementedError('I should do a low level check!')

class RedisBackendTestUtils(BackendTestUtils):
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

    @classmethod
    def tearDownClass(cls):
        b = backends.RedisBackend(prefix='test_subscription')
        for key in b.redis.keys('test*'):
            b.redis.delete(key)

    def assertStateQueueLengthEqual(self, expected, state, queue='default'):
        result = self.b.redis.lrange(
            self.b.get_key(self.u, state, queue), 0, -1)
        self.assertEqual(expected, len(result))

class FacebookStory(object):
    def test_000_notification_list_page(self):
        """
        This tests the backend method get_all_notifications, used to make a
        page like facebook.com/notifications which displays a list of all
        notifications, and pushes them to the third state (above undelivered
        and unacknowledged which your states should look like)
        """
        self.b.user_emit(self.u, 'x follows you', {}, {'timestamp': 1}, 
            'friends')
        self.b.user_emit(self.u, 'x commented on your status update', {}, 
            {'timestamp': 2}, 'chat')
        self.b.user_emit(self.u, 'y follows you', {}, {'timestamp': 3}, 
            'friends')

        result = self.b.get_all_notifications(self.u, 
            # this keyword argument must be set if setting
            # SUBSCRIPTION_NOTIFICATION_QUEUES does not match the default
            # queues you want the backend to work on. Otherwise, this kwarg
            # is not required.
            queues=['chat', 'friends'])

        expected = [
            {
                'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                'initial_state': 'undelivered',
                'queue': 'friends',
                'text': u'x follows you',
                'timestamp': 1
            },
            {
                'datetime': datetime.datetime(1969, 12, 31, 18, 0, 2),
                'initial_state': 'undelivered',
                'queue': 'chat',
                'text': u'x commented on your status update',
                'timestamp': 2
            },
            {
                'datetime': datetime.datetime(1969, 12, 31, 18, 0, 3),
                'initial_state': 'undelivered',
                'queue': 'friends',
                'text': u'y follows you',
                'timestamp': 3
            }
        ]
        
        self.assertEqual(expected, result)

        # the default behaviour of get_all_notifications is to push each
        # notification to the third state. Let's see if that works:
        self.assertStateQueueLengthEqual(0, 'undelivered', 'chat')
        self.assertStateQueueLengthEqual(0, 'undelivered', 'friends')
        self.assertStateQueueLengthEqual(0, 'unacknowledged', 'chat')
        self.assertStateQueueLengthEqual(0, 'unacknowledged', 'friends')
        self.assertStateQueueLengthEqual(1, 'acknowledged', 'chat')
        self.assertStateQueueLengthEqual(2, 'acknowledged', 'friends')

    def test_001_live_notification(self):
        """
        This tests the backend method get_last_notifications, which is used by
        javascript to prepend the new (undelivered) notifications only.
        
        This method should, by default:

        - return all notifications of the first state
        - groupped by queue
        - with updated counts per queue and total
        - in reverse order by default, because javascript wants to prepend 
          oldest first
        - push those notifications from the first to the second state
        """
        self.b.user_emit(self.u, 'x sent a private message', {}, 
            {'timestamp': 5}, 'chat')
        
       # the javascript polls the view that calls:
        result = self.b.get_last_notifications(self.u, queues=['chat', 'friends'], minimal=True)
        expected = {
            'chat': {
                'counts': {
                    'acknowledged': 1,
                    'total': 2,
                    'unacknowledged': 0,
                    'undelivered': 1
                },
                'notifications': [
                    {
                        'initial_state': 'undelivered',
                        'text': u'x sent a private message',
                        'timestamp': 5
                    }
                ]
            },
             'friends': {
                'counts': {
                    'acknowledged': 2,
                    'total': 2,
                    'unacknowledged': 0,
                    'undelivered': 0
                },
                'notifications': []
            }
        }

        self.assertEqual(expected, result)

        # let's make sure that the push to unacknowledged worked
        self.assertStateQueueLengthEqual(0, 'undelivered', 'chat')
        self.assertStateQueueLengthEqual(0, 'undelivered', 'friends')
        self.assertStateQueueLengthEqual(1, 'unacknowledged', 'chat')
        self.assertStateQueueLengthEqual(0, 'unacknowledged', 'friends')
        self.assertStateQueueLengthEqual(1, 'acknowledged', 'chat')
        self.assertStateQueueLengthEqual(2, 'acknowledged', 'friends')

 
    def test_002_push(self):
        """
        This tests the push_state method which should called by javascript
        (throught a django view of course) when the user clicks to activate the
        dropdown, acknowledging all notifications up to the last one that is
        displayed in the dropdown. 
        """
        # user clicks to see the 'chat' queue dropdown:
        self.b.push_state(self.u, 'unacknowledged', 'chat')
        
        self.assertStateQueueLengthEqual(0, 'undelivered', 'chat')
        self.assertStateQueueLengthEqual(0, 'unacknowledged', 'chat')
        self.assertStateQueueLengthEqual(2, 'acknowledged', 'chat')

    def test_003_page_reload(self):
        """
        This tests a usage of get_last_notifications done by the
        subscription_yourlabs_widget template tag. Basically, it should display
        a number of last notifications. In our case: 3.
        """

        self.b.user_emit(self.u, 'y sent a private message', {}, 
            {'timestamp': 10}, 'chat')
        self.b.user_emit(self.u, 'z sent a private message', {}, 
            {'timestamp': 10}, 'chat')

        result = self.b.get_last_notifications(self.u, 
            # any state will do, we just want that dropdown filled
            states=['undelivered', 'unacknowledged', 'acknowledged'], 
            queues=['chat', 'friends'], queue_limit=3)
        
        expected = {
            'chat': {
                'counts': {
                    'acknowledged': 2,
                    'total': 4,
                    'unacknowledged': 0,
                    'undelivered': 2
                },
            'notifications': [
                {
                    'datetime': datetime.datetime(1969, 12, 31, 18, 0, 11),
                    'initial_state': 'undelivered',
                    'text': u'z sent a private message',
                    'timestamp': 11
                },
                {
                    'datetime': datetime.datetime(1969, 12, 31, 18, 0, 10),
                    'initial_state': 'undelivered',
                    'text': u'y sent a private message',
                    u'timestamp': 10
                },
                {
                    'datetime': datetime.datetime(1969, 12, 31, 18, 0, 5),
                    'initial_state': 'acknowledged',
                    'text': u'x sent a private message',
                    'timestamp': 5
                }
            ]
        },
        'friends': {
                'counts': {
                    'acknowledged': 2,
                    'total': 2,
                    'unacknowledged': 0,
                    'undelivered': 0
                },
                'notifications': [
                    {
                        'datetime': datetime.datetime(1969, 12, 31, 18, 0, 3),
                        'initial_state': 'acknowledged',
                         'text': u'y follows you',
                         'timestamp': 3
                    }, 
                    {
                        'datetime': datetime.datetime(1969, 12, 31, 18, 0, 1),
                        'initial_state': 'acknowledged',
                        'text': u'x follows you',
                        'timestamp': 1
                    }
                ]
            }
        }
        self.assertEqual(expected, result)

class FacebookStoryRedisTest(RedisBackendTestUtils, FacebookStory, unittest.TestCase):
    pass

class RedisBackendTest(RedisBackendTestUtils, unittest.TestCase):
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
        self.assertEqual(['text', 'important'], actual.keys())
        
        actual = self.b.unserialize(value, True)
        self.assertEqual(['text', 'important'], actual.keys())

        fixture[3]['timestamp'] = 1316504374
        expected = {
            'timestamp': 1316504374.0, 
            'important': 'foo', 
            'text': 'foo',
            'datetime': datetime.datetime(2011, 9, 20, 2, 39, 34),
        }
        value = self.b.serialize(*fixture)
        actual = self.b.unserialize(value)
        self.assertEqual(expected, actual)

    def test_user_emit(self):
        self.b.user_emit(self.u, 'foo', {}, {'x': 'y'})
        result = self.b.redis.lrange(
            self.b.get_key(1, 'undelivered', 'default'), 0, -1)
        self.assertEqual(1, len(result))

    def test_push_state(self):
        self.b.user_emit(self.u, 'foo', kwargs={'timestamp':1})
        self.assertStateQueueLengthEqual(1, 'undelivered')
        self.assertStateQueueLengthEqual(0, 'unacknowledged')
        self.assertStateQueueLengthEqual(0, 'acknowledged')

        self.b.push_state(self.u, 'undelivered')
        self.assertStateQueueLengthEqual(0, 'undelivered')
        self.assertStateQueueLengthEqual(1, 'unacknowledged')
        self.assertStateQueueLengthEqual(0, 'acknowledged')

        self.b.push_state(self.u, 'unacknowledged')
        self.assertStateQueueLengthEqual(0, 'undelivered')
        self.assertStateQueueLengthEqual(0, 'unacknowledged')
        self.assertStateQueueLengthEqual(1, 'acknowledged')

    def test_push_state_with_noise(self):
        self.b.user_emit(self.u, 'foo', kwargs={'timestamp':1})
        self.b.user_emit(self.u, 'foo', kwargs={'timestamp':1})
        self.assertStateQueueLengthEqual(2, 'undelivered')
        self.assertStateQueueLengthEqual(0, 'unacknowledged')
        self.assertStateQueueLengthEqual(0, 'acknowledged')

        self.b.push_state(self.u, 'undelivered')
        self.assertStateQueueLengthEqual(0, 'undelivered')
        self.assertStateQueueLengthEqual(2, 'unacknowledged')
        self.assertStateQueueLengthEqual(0, 'acknowledged')

        self.b.user_emit(self.u, 'foo', kwargs={'timestamp':1})
        self.b.push_state(self.u, 'unacknowledged')
        self.assertStateQueueLengthEqual(1, 'undelivered')
        self.assertStateQueueLengthEqual(0, 'unacknowledged')
        self.assertStateQueueLengthEqual(2, 'acknowledged')
