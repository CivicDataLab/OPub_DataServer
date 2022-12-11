import mimetypes
import os
import magic

from django.http import HttpResponse

from dataset_api.models.DataAccessModel import DataAccessModel


def download(request, model_id):
    model = DataAccessModel.objects.get(pk=model_id)
    file_path = model.contract.path
    if len(file_path):
        mime_type = magic.from_file(file_path, mime=True)
        response = HttpResponse(model.contract, content_type=mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
    else:
        response = HttpResponse("file doesnt exist", content_type='text/plain')
    return response
