from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from subscription.models import Subscription
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required

from django.contrib import messages

def subscribe(request,content_type,object_id,success_message="Subscription added"):
	content_type = get_object_or_404(ContentType,pk=content_type)
	if not request.user.is_authenticated():
		raise Http404

	Subscription.objects.get_or_create(content_type=content_type,object_id=object_id,user=request.user)
	messages.success(request,success_message)
	return redirect(request.GET.get('return_url','/'))

def unsubscribe(request,content_type,object_id,success_message="You have been unsubscribed"):
	content_type = get_object_or_404(ContentType,pk=content_type)
	if not request.user.is_authenticated():
		raise Http404

	subscription = get_object_or_404(Subscription,content_type=content_type,object_id=object_id,user=request.user)
	subscription.delete()
	messages.success(request,success_message)
	return redirect(request.GET.get('return_url','/'))

class SubscriptionView(ListView):
    paginate_by = 25
    ordering = ['timestamp']
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
            return super(SubscriptionView, self).dispatch(*args, **kwargs)
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('-timestamp')
