from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from subscription.models import Subscription

def subscribe(request,content_type,object_id,success_message="Subscription added"):
	content_type = get_object_or_404(ContentType,pk=content_type)
	if not request.user.is_authenticated():
		raise Http404

	Subscription.objects.get_or_create(content_type=content_type,object_id=object_id,user=request.user)
	request.user.message_set.create(message=success_message)
	return redirect(request.GET.get('return_url','/'))

def unsubscribe(request,content_type,object_id,success_message="You have been unsubscribed"):
	content_type = get_object_or_404(ContentType,pk=content_type)
	if not request.user.is_authenticated():
		raise Http404

	subscription = get_object_or_404(Subscription,content_type=content_type,object_id=object_id,user=request.user)
	subscription.delete()
	request.user.message_set.create(message=success_message)
	return redirect(request.GET.get('return_url','/'))

def subscriptions_for_user(request,user,queryset=None):
	if not queryset:
		queryset = Subscription.objects.all()

	from django.views.generic.list_detail import object_list
	return object_list(request,queryset.filter(user=user))
