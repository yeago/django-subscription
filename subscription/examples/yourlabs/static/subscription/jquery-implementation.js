Subscription = function(url, override) {
    instance = $.extend({
        'delay': 3000,
        'url': url,
        'states': ['undelivered', 'unacknowledged', 'acknowledged'],
        'refresh': function() {
            var url = Subscription.singleton.url + '?x=' + Math.round(new Date().getTime());
            $.getJSON(url, function(data, text_status, jq_xhr) {
                for(var state in Subscription.singleton.states) {
                    state = Subscription.singleton.states[state];
                    for(var key in data[state]) {
                        var notification = data[state][key];
                        var el = $('.subscription .'+notification.kwargs.kind+' .list')
                        if (! el.find('.' + notification.timestamp).length) {
                            var html = '<div class="notification '+notification.timestamp+' '+state+'">'+notification.text+'</div>';
                            el.prepend(html);
                            $('.'+notification.timestamp+'.'+state).find('a.acknowledge').each(function() {
                                $(this).attr('href', $(this).attr('href') + '?acknowledge=' + notification.timestamp);
                            });

                            // pop last one ?
                            var show_more = false;
                            while (el.find('.notification').length > 10) {
                                // horrible hack
                                el.find('.notification:last').remove();
                                show_more = true;
                            }
                            if (show_more) {
                                $('.subscription .'+notification.kwargs.kind+' .more').show();
                            }
                        }
                    }

                    for(var queue in Subscription.singleton.queues) {
                        queue = Subscription.singleton.queues[queue];
                        var count = $('.subscription .' + queue + ' .list .undelivered').length + $('.subscription .' + queue + ' .list .unacknowledged').length;
                        $('.subscription .' + queue + ' .count').html(count);
                    }
                }
            }).fail(Subscription.singleton.set_timeout)
              .done(Subscription.singleton.set_timeout);
        },
        'set_timeout': function() {
            setTimeout(function() {
                Subscription.singleton.refresh()
            }, Subscription.singleton.delay);
        },
    }, override);

    return instance
}

Subscription.factory = function(url, override) {
    Subscription.singleton = Subscription(url, override);
    Subscription.singleton.refresh();
}
