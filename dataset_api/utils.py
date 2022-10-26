from django.utils.text import slugify
from numpy.compat import unicode

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
