Subscription = function(json_url, push_url, override) {
    instance = $.extend({
        'delay': 3000,
        'json_url': json_url,
        'push_url': push_url,
        'queue_limit': 10,
        'setup_dropdown': function() {
            $('.subscription .queue .toggler').click(function() {
                var dropdown = $(this).parents('.queue').find('.dropdown');

                if (dropdown.css('display') == 'block') {
                    dropdown.slideUp();
                } else {
                    dropdown.slideDown();

                    var queue_name = Subscription.singleton.get_queue_name($(this));
                    var counter = $('.subscription .'+queue_name+' .count.unacknowledged');
                    var count = parseInt(counter.html());

                    if (counter > 0) {
                        counter.html(0);
                        $.get(Subscription.singleton.push_url, {
                            'queue': queue_name,
                        });
                    }
                }
            });
            $('.subscription .dropdown').hover(function() {
                Subscription.singleton.mouse_inside = true;
            }, function() {
                Subscription.singleton.mouse_inside = false;
            });
            $(document).mouseup(function() {
                if (!Subscription.singleton.mouse_inside) {
                    $('.subscription .dropdown:visible').slideUp();
                }
            });
        },
        'display': function(queues) {
            var queue, notification;
            console.log(queues)

            for(var queue_name in queues) {
                queue = queues[queue_name];
                
                $('.subscription .queue.'+queue_name+' .count.unacknowledged').html(queue['count']);

                if (queue['dropdown'] !== undefined) {
                    $('.subscription .queue.'+queue_name+' .dropdown').html(queue['dropdown']);
                }
            }
        },
        'refresh': function() {
            var json_url = Subscription.singleton.json_url + '?x=' + Math.round(new Date().getTime());
            $.getJSON(json_url, function(queues, text_status, jq_xhr) {
                Subscription.singleton.display(queues);
            }).fail(Subscription.singleton.set_timeout)
              .done(Subscription.singleton.set_timeout);
        },
        'set_timeout': function() {
            setTimeout(function() {
                Subscription.singleton.refresh()
            }, Subscription.singleton.delay);
        },
        'get_queue_name': function(el) {
            var queue_el = el.is('.queue') ? el : el.parents('.queue');
            return queue_el.attr('id').match(/subscription_queue_(.+)$/)[1];
        },
        'get_last_timestamp': function(queue) {
            var el = $('#subscription_queue_' + queue + ' .notification:first');
            return Subscription.singleton.get_timestamp_from_notification(el);
        },
        'get_timestamp_from_notification': function(el) {
            var notification_el = el.is('.notification') ? el : el.parents('.notification');
            return notification_el.attr('id').match(/timestamp_([0-9]+)/)[1];
        },
    }, override);

    return instance
}

Subscription.factory = function(json_url, push_url, override) {
    Subscription.singleton = Subscription(json_url, push_url, override);
    Subscription.singleton.setup_dropdown();
    Subscription.singleton.refresh();
}
