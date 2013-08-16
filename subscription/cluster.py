import datetime
from django.template.defaultfilters import pluralize
from django.conf import settings


def render_actors(actors):
    """
    Gives the following experience

    1 actor     -   SomeBody commented on X
    2 actors    -   SomeBody and AnotherPerson commented on X
    >2 actors   -   SomeBody, AnotherPerson and 3 others commented on X
    """
    actors = map(dict, set(tuple(sorted(d.items())) for d in actors))
    # http://stackoverflow.com/questions/11092511/python-list-of-unique-dictionaries
    join_on = ", "
    if len(actors) == 2:
        join_on = " and "
    string = join_on.join(i['displayName'] for i in actors[:2])
    if len(actors) > 2:
        string = "%s and %s other%s" % (string, len(actors) - 2, pluralize(len(actors) -2))
    return string

def cluster_specs(specs):
    clusters = {}
    for spec in specs:
        try:
            object_id = int(spec['target']['objectId'])
        except ValueError:
            object_id = spec['target']['objectId']
        key = (spec['target']['objectType'], object_id, spec['verb'])
        if not key in clusters:
            clusters[key] = []
        clusters[key].append(spec)
    return render_clusters(clusters)

def render_clusters(clusters):
    for cluster in clusters.values():
        formatting = {}
        formatting['actor'] = render_actors([i['actor'] for i in cluster if i['actor'].get('displayName')])
        formatting['target'] = cluster[0]['target']['displayName']
        verbage = settings.SUBSCRIPTION_VERB_RENDER_MAP[cluster[0]['verb']] % formatting
        yield datetime.datetime.fromtimestamp(max(i["published"] for i in cluster)), verbage
