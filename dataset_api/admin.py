from django.contrib import admin

# Register your models here.

from .models import Organization, Catalog, Dataset, Resource

admin.site.register(Organization)
admin.site.register(Catalog)
admin.site.register(Dataset)
admin.site.register(Resource)
