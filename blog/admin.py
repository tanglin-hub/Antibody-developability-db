from django.contrib import admin
from .models import Antibody
from import_export import resources
from import_export.admin import ExportMixin
# Register your models here.


class AntibodyResources(resources.ModelResource):
    class Meta:
        model=Antibody

class AntibodyAdmin(ExportMixin,admin.ModelAdmin):
    resource_class=AntibodyResources



admin.site.register(Antibody,AntibodyAdmin)    