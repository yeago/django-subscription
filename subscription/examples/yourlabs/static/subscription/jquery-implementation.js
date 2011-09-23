Subscription = function(json_url, push_url, override) {
    instance = $.extend({
        'delay': 3000,
        'json_url': json_url,
        'push_url': push_url,
        'queue_limit': 10,
        'last_data': {},
        'setup_dropdown': function() {
            $('.subscription .queue .toggler').click(function() {
                var dropdown = $(this).parents('.queue').find('.dropdown');

                if (dropdown.css('display') == 'block') {
                    dropdown.slideUp();
                } else {
                    dropdown.slideDown();

                    var queue_name = Subscription.singleton.get_queue_name($(this));
                    if (Subscription.singleton.last_data[queue_name]['counts']['unacknowledged'] > 0) {
                        Subscription.singleton.display_count('unacknowledged', queue_name, '0');
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
        'display_count': function(state, queue, count) {
            $('.subscription .'+queue+' .count.'+state).html(count);
            if (state == 'acknowledged' && count > 0) {
                $('.subscription .queue.'+queue+' .more').show();
            }
        },
        'display_notification': function(queue, notification) {
            $('.subscription .'+queue+' .list').prepend(
                '<div class="notification '+notification.timestamp+' '+notification.state+'">'+notification.text+'</div>'
            );
            if ($('.subscription .'+queue+' .list .notification').length > Subscription.singleton.queue_limit) {
                $('.subscription .'+queue+' .list .notification:last').remove();
            }
        },
        'refresh': function() {
            var json_url = Subscription.singleton.json_url + '?x=' + Math.round(new Date().getTime());
            $.getJSON(json_url, function(data, text_status, jq_xhr) {
                var queue, notification;

                Subscription.singleton.last_data = data;

                for(var queue_name in data) {
                    queue = data[queue_name];
                    
                    for (var state_name in queue['counts']) {
                        Subscription.singleton.display_count(state_name, queue_name, queue['counts'][state_name]);
                    }

                    for (var notification_key in queue['notifications']) {
                        notification = queue['notifications'][notification_key];
                        Subscription.singleton.display_notification(queue_name, notification);
                    }
                }
                return true;
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
