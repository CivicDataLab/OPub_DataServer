import mimetypes
import os

from django.http import HttpResponse

from dataset_api.data_request.models import DataRequest


def download(request, data_request_id):
    request = DataRequest.objects.get(pk=data_request_id)
    file_path = request.file.path
    if len(file_path):
        mime_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(request.file, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
        # TODO: delete file after download
        # request.file
        # request.save()
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
