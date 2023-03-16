import mimetypes
import os
import magic

from django.http import HttpResponse

from dataset_api.models.License import License
from django.core.files.storage import default_storage

def download(request, license_id):
    license = License.objects.get(pk=license_id)
    file_path = "/" + license.file.name
    if default_storage.exists(file_path):
        mime_type = magic.from_buffer(license.file.read(), mime=True)
        response = HttpResponse(license.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
