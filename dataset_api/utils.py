from django.db.models import Avg
from django.utils.text import slugify
from numpy.compat import unicode

from activity_log.signal import activity
from dataset_api.enums import RatingStatus
from dataset_api.models import Dataset


def get_client_ip(request):
    x_forwarded_for = request.context.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.context.META.get('REMOTE_ADDR')
    return ip


def dataset_slug(dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    return slugify(unicode('%s_%s' % (dataset.title, dataset_id)))


def log_activity(target_obj, verb, target_group=None, username="anonymous", ip=""):
    activity.send(
        username, verb=verb, target=target_obj, target_group=target_group, ip=ip
    )


def get_average_rating(dataset):
    ratings = dataset.datasetratings_set.filter(status=RatingStatus.PUBLISHED.value).aggregate(Avg('data_quality'))[
        'data_quality__avg']
    return ratings if ratings else 0


def get_keys(json_obj, keys_list):
    if isinstance(json_obj, dict):
        keys_list += json_obj.keys()
        map(lambda x: get_keys(x, keys_list), json_obj.values())
    elif isinstance(json_obj, list):
        map(lambda x: get_keys(x, keys_list), json_obj)
