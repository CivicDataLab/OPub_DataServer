import os
import magic
import mimetypes

from django.http import HttpResponse
from dataset_api.models import Resource


def download(request, resource_id):
    resource = Resource.objects.get(pk=resource_id)
    file_path = resource.filedetails.file.name
    if len(file_path):
        mime_type = magic.from_buffer(resource.filedetails.file.read(), mime=True)
        response = HttpResponse(resource.filedetails.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
