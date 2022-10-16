import mimetypes
import os

from django.http import HttpResponse

from dataset_api.models import License


def download(request, license_id):
    license = License.objects.get(pk=license_id)
    file_path = license.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(license.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
