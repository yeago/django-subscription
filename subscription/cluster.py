from django.template.defaultfilters import pluralize
from django.conf import settings


def render_actors(actors):
    """
    Gives the following experience

    1 actor     -   SomeBody commented on X
    2 actors    -   SomeBody and AnotherPerson commented on X
    >2 actors   -   SomeBody, AnotherPerson and 3 others commented on X
    """
    # http://stackoverflow.com/questions/11092511/python-list-of-unique-dictionaries
    unique_actors = map(dict, set(tuple(sorted(d.items())) for d in actors))
    #  But we need them in the original order since its timestamped
    unique_redux = []
    for actor in actors:
        for unique in unique_actors:
            if unique == actor and unique not in unique_redux:
                unique_redux.append(unique)
                break
    actors = unique_redux
    join_on = ", "
    if len(actors) == 2:
        join_on = " and "
    string = join_on.join(i['displayName'] for i in actors[:2])
    if len(actors) > 2:
        string = "%s and %s other%s" % (string, len(actors) - 2, pluralize(len(actors) - 2))
    return string


def cluster_specs(specs):
    clusters = {}

    for spec in specs:
        try:
            object_id = int(spec['target']['objectId'])
        except ValueError:
            object_id = spec['target']['objectId']
        key = (spec['target']['objectType'], object_id, spec['verb'])
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(spec)
    return clusters


def render_clusters(specs):
    for cluster, items in specs.items():
        items = sorted(items, key=lambda x: x['published'], reverse=True)
        formatting = {}
        if cluster[2] in settings.NON_CLUSTER_SUBSCRIPTION_VERBS:
            for item in items:
                if item.get('actor'):
                    formatting['actor'] = item['actor'].get('displayName') or ''
                if item.get('target'):
                    formatting['target'] = item['target'].get('displayName') or ''
                try:
                    yield item['published'], settings.SUBSCRIPTION_VERB_RENDER_MAP[item['verb']] % formatting
                except KeyError:
                    continue
        else:
            try:
                formatting['actor'] = render_actors([i['actor'] for i in items if i['actor'].get('displayName')])
            except KeyError:
                continue
            formatting['target'] = items[0]['target']['displayName']
            verbage = settings.SUBSCRIPTION_VERB_RENDER_MAP[items[0]['verb']] % formatting
            yield max(i["published"] for i in items), verbage
