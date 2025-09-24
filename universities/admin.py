from django.contrib import admin
from django.contrib import messages
from .models import University, UserDashboard, UniversityJSONImport
from .serializers import UniversitySerializer
import json

# Register your models here.
admin.site.register(University)
admin.site.register(UserDashboard)

@admin.register(UniversityJSONImport)
class UniversityJSONImportAdmin(admin.ModelAdmin):
    """
    Custom admin view to allow creating universities by pasting JSON data.
    """
    list_display = ('created_at',)
    ordering = ('-created_at',)
    # Define fields for the "add" page
    fields = ('json_data',)

    def save_model(self, request, obj, form, change):
        # We save the import object itself to have a history.
        super().save_model(request, obj, form, change)

        json_data_str = form.cleaned_data.get('json_data')
        if not json_data_str:
            self.message_user(request, "JSON data field cannot be empty.", level=messages.WARNING)
            return

        try:
            data = json.loads(json_data_str)
            is_many = isinstance(data, list)
            
            serializer = UniversitySerializer(data=data, many=is_many)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            count = len(data) if is_many else 1
            self.message_user(request, f"Successfully imported {count} university/universities.", level=messages.SUCCESS)
        except Exception as e:
            # This will catch JSONDecodeError, serializer validation errors, etc.
            self.message_user(request, f"An error occurred during import: {e}", level=messages.ERROR)

    def has_change_permission(self, request, obj=None):
        # This view is for adding (importing) only. No editing of past imports.
        return False
