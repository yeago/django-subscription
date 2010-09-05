from django.template import Library
from django.core.urlresolvers import reverse

from django.contrib.contenttypes.models import ContentType
from subscription.models import Subscription

register = Library()

@register.simple_tag
def unsubscribe_url(instance):
	ct = ContentType.objects.get_for_model(instance.__class__)
	return reverse("subscribe",[ct,instance.pk])

@register.simple_tag
def subscribe_url(instance):
	ct = ContentType.objects.get_for_model(instance.__class__)
	return reverse("unsubscribe",[ct,instance.pk])

@register.simple_tag
def subscription_toggle_link(object, user, return_url=None):
	if not user.is_authenticated():
		return ''

	ct = ContentType.objects.get_for_model(object.__class__)
	try:
		Subscription.objects.get(content_type=ct,object_id=object.pk,user=user)
		url = "subscription_unsubscribe"
		verbage = "Unsubscribe"
	except Subscription.DoesNotExist:
		url = "subscription_subscribe"
		verbage = "Subscribe"

	except Subscription.MultipleObjectsReturned:
		url = "subscription_unsubscribe"
		verbage = "Unsubscribe"
	
	if return_url:
		return "<a href='%s?return_url=%s'>%s</a>" % (reverse(url,args=[ct.pk,object.pk]),return_url,verbage)
	return "<a href='%s'>%s</a>" % (reverse(url,args=[ct.pk,object.pk]),verbage)

