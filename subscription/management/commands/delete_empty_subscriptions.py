from django.core.management.base import BaseCommand

from subscription.models import Subscription


def queryset_iterator(queryset, chunksize=1000):
    '''''
    Iterate over a Django Queryset ordered by the primary key
    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.
    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    try:
        last_pk = queryset.order_by('-pk')[0].pk
    except IndexError:
        pass
    else:
        queryset = queryset.order_by('pk')
        while pk < last_pk:
            for row in queryset.filter(pk__gt=pk)[:chunksize]:
                pk = row.pk
                yield row


class Command(BaseCommand):
    args = ""
    help = "Deletes all subscriptions with None as content_object"

    def handle(self, *args, **options):
        deleted_subscriptions_counter = 0
        total_subscriptions_counter = 0
        subscription_iterator = queryset_iterator(Subscription.objects.all())
        for subscription in subscription_iterator:
            total_subscriptions_counter += 1
            try:
                if subscription.content_object is None:
                    subscription.delete()
                    deleted_subscriptions_counter += 1
            except AttributeError:
                subscription.delete()
                deleted_subscriptions_counter += 1

        self.stdout.write('Total subscriptions: %s\nSuccessfully deleted subscriptions: %s\n' %
                          (total_subscriptions_counter, deleted_subscriptions_counter))
