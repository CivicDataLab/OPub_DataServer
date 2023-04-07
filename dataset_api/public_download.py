import mimetypes
import os
import magic
import copy

from django.http import HttpResponse

from django.core.files.storage import default_storage


def download(request, file_path):

    print ('--------path', file_path)
    file_path = '/' + file_path
    if  default_storage.exists(file_path):
        file = default_storage.open(file_path, 'rb').read()
        file_copy = copy.deepcopy(file)
        mime_type = magic.from_buffer(file_copy, mime=True)
       
        
        response = HttpResponse(file, content_type=mime_type)
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
