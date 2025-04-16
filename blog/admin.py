from django.contrib import admin
from .models import Antibody,Feedback
from import_export import resources
from import_export.admin import ExportMixin
# Register your models here.


class AntibodyResources(resources.ModelResource):
    class Meta:
        model=Antibody

class AntibodyAdmin(ExportMixin,admin.ModelAdmin):
    resource_class=AntibodyResources

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')  # 显示在列表中的字段
    search_fields = ('email', 'content')   # 可搜索的字段
    ordering = ('-created_at',)            # 按提交时间倒序排列

admin.site.register(Antibody,AntibodyAdmin)    