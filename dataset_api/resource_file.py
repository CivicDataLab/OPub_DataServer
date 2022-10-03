import os

from django.http import HttpResponse
import mimetypes
from dataset_api.models import Resource


def download(request, resource_id):
    resource = Resource.objects.get(pk=resource_id)
    file_path = resource.filedetails.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(resource.filedetails.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
