import mimetypes
import os
import magic
import copy

from django.http import HttpResponse

from django.core.files.storage import default_storage


def download(request, file_path):
    if  default_storage.exists(file_path):
        file = default_storage.open(file_path, 'r')
        
        file_copy = copy.deepcopy(file)
        mime_type = magic.from_file(file_copy, mime=True)
        
        response = HttpResponse(file, content_type=mime_type)
        # response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
