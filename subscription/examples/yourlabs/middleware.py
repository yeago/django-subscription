from subscription_backends import SiteBackend

class AcknowledgeMiddleware(object):
    def process_request(self, request):
        if not request.user.is_authenticated():
            return

        if 'subscription_timestamp' in request.GET.keys():
            b = SiteBackend()
            b.push_notification(request.user,
                request.GET['subscription_timestamp'],
                request.GET.get('subscription_queue', 'default'),
            )
