import os

from django.http import HttpResponse
import mimetypes
from dataset_api.models import Organization


def logo(request, organization_id):
    org_instance = Organization.objects.get(pk=organization_id)
    file_path = org_instance.logo.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(org_instance.logo.path, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
