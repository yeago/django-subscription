Subscription = function(json_url, push_url, override) {
    instance = $.extend({
        'delay': 7000,
        'json_url': json_url,
        'push_url': push_url,
        'counts': {},
        'setup_dropdown': function() {
            $('.subscription .toggler').live('click', function() {
                var dropdown = $(this).parent().find('.dropdown.inner');

                if (dropdown.css('display') == 'block') {
                    dropdown.slideUp();
                } else {
                    dropdown.slideDown();

                    var dropdown_name = Subscription.singleton.get_dropdown_name($(this));
                    var counter = $(this).find('.counter')

                    if (parseInt(counter.html()) > 0) {
                        counter.html('0');
                        $.get(Subscription.singleton.push_url, {
                            'dropdown': dropdown_name,
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
                    $('.subscription .dropdown.inner:visible').slideUp();
                }
            });
            Subscription.singleton.update_counts();
        },
        'display': function(dropdowns) {
            for(var dropdown_name in dropdowns) {
                var wrapper = $('#subscription_dropdown_' + dropdown_name);
                wrapper.html(dropdowns[dropdown_name]);
            }
            Subscription.singleton.update_counts();
        },
        'refresh': function() {
            var data = {
                /* stupid browser cache workaround */
                'x': Math.round(new Date().getTime()),
            }
            for (var dropdown_name in Subscription.singleton.counts) {
                data[dropdown_name] = Subscription.singleton.counts[dropdown_name];
           }

            $.getJSON(Subscription.singleton.json_url, data,
                function(dropdowns, text_status, jq_xhr) {
                    Subscription.singleton.display(dropdowns);
            }).fail(Subscription.singleton.set_timeout)
              .done(Subscription.singleton.set_timeout);
        },
        'set_timeout': function() {
            setTimeout(function() {
                Subscription.singleton.refresh()
            }, Subscription.singleton.delay);
        },
        'get_dropdown_name': function(el) {
            var dropdown_el = el.is('.dropdown') ? el : el.parents('.dropdown');
            return dropdown_el.attr('id').match(/subscription_dropdown_(.+)$/)[1];
        },
        'update_counts': function() {
            $('.subscription .dropdown.outer').each(function() {
                var s = Subscription.singleton;
                var c = parseInt($(this).find('.counter').html());
                s.counts[s.get_dropdown_name($(this))] = c;
            });
        },
    }, override);

    return instance
}

Subscription.factory = function(json_url, push_url, override) {
    Subscription.singleton = Subscription(json_url, push_url, override);
    Subscription.singleton.setup_dropdown();
    Subscription.singleton.refresh();
}
