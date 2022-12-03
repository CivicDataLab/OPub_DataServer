from django.db.models import Avg
from django.utils.text import slugify
from django.conf import settings
from numpy.compat import unicode

from activity_log.signal import activity
from dataset_api.enums import RatingStatus
from dataset_api.models import Dataset, DataAccessModel


def get_client_ip(request):
    x_forwarded_for = request.context.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.context.META.get("REMOTE_ADDR")
    return ip


def dataset_slug(dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    return slugify(unicode("%s_%s" % (dataset.title, dataset_id)))


def log_activity(target_obj, verb, target_group=None, username="anonymous", ip=""):
    activity.send(
        username, verb=verb, target=target_obj, target_group=target_group, ip=ip
    )


def get_average_rating(dataset):
    ratings = dataset.datasetratings_set.filter(
        status=RatingStatus.PUBLISHED.value
    ).aggregate(Avg("data_quality"))["data_quality__avg"]
    return ratings if ratings else 0


def get_keys(json_obj, keys_list):
    if isinstance(json_obj, dict):
        keys_list += json_obj.keys()
        map(lambda x: get_keys(x, keys_list), json_obj.values())
    elif isinstance(json_obj, list):
        map(lambda x: get_keys(x, keys_list), json_obj)


def idp_make_cache_key(group, window, rate, value, methods):
    # Same values from all arguments - {dataset_api.data_request.data_request_file.download 1668506571 12/7d Archit||1 (None,)}
    print("---g1--", group)
    group = group.split("||")
    print("---g2--", group)
    rate = rate.split("/")[1]
    prefix = getattr(settings, "RATELIMIT_CACHE_PREFIX", "rl||")
    print(prefix + value + "||" + rate + "||" + group[0])
    return prefix + value + "||" + rate + "||" + group[0]


def remove_a_key(d, remove_key):
    for key in list(d.keys()):
        if key not in remove_key:
            del d[key]
        else:
            skip_col(d[key], remove_key)


def skip_col(d, remove_key):
    if isinstance(d, dict):
        remove_a_key(d, remove_key)
    if isinstance(d, list):
        for each in d:
            if isinstance(each, dict):
                remove_a_key(each, remove_key)

    return d


def clone_object(obj, attrs={}):

    print("----clone", obj)

    # we start by building a "flat" clone
    clone = obj._meta.model.objects.get(pk=obj.pk)
    clone.pk = None

    # if caller specified some attributes to be overridden,
    # use them
    for key, value in attrs.items():
        setattr(clone, key, value)

    # save the partial clone to have a valid ID assigned
    clone.save()

    # Scan field to further investigate relations
    fields = clone._meta.get_fields()
    for field in fields:

        # Manage M2M fields by replicating all related records
        # found on parent "obj" into "clone"
        if not field.auto_created and field.many_to_many:
            for row in getattr(obj, field.name).all():
                getattr(clone, field.name).add(row)

        # Manage 1-N and 1-1 relations by cloning child objects
        if field.auto_created and field.is_relation:
            if field.many_to_many:
                # do nothing
                pass
            else:
                # provide "clone" object to replace "obj"
                # on remote field
                attrs = {field.remote_field.name: clone}
                children = field.related_model.objects.filter(
                    **{field.remote_field.name: obj}
                )
                for child in children:
                    print("🍤🍤🍤", str(child._meta.object_name))
                    print(
                        "💪💪💪",
                        str(child._meta.object_name)
                        not in [
                            "DataRequest",
                            "Geography",
                            "Sector",
                            "Catalog",
                            "DatasetReviewRequest",
                            "Tag",
                            "DatasetAccessModelRequest",
                        ],
                    )
                    if str(child._meta.object_name) not in [
                        "DataRequest",
                        "Geography",
                        "Sector",
                    ]:
                        # if child not in ["DataRequest", "Geography", "Sector"]:
                        clone_object(child, attrs)

    return clone


def cloner(object_type, object_id):
    obj = object_type.objects.get(pk=object_id)
    # data = {"id": str(obj.pk)}

    print("---in----")
    clone = clone_object(obj)
    print("---out----")

    return clone.id
