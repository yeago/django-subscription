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
def subscription_toggle_url(instance, user):
	ct = ContentType.objects.get_for_model(instance.__class__)
	try:
		Subscription.objects.get(content_type=ct,object_id=instance.pk,user=user)
		url = "subscription_unsubscribe"
		verbage = "Unsubscribe"
	except Subscription.DoesNotExist:
		url = "subscription_subscribe"
		verbage = "Subscribe"

	return "<a href='%s'>%s</a>" % (reverse(url,args=[ct.pk,instance.pk]),verbage)

