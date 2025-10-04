from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import University, UserDashboard, UniversityJSONImport, ScholarshipResult
from .serializers import UniversitySerializer
from .scholarship_service import ScholarshipOwlService
import json

# Register your models here.
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

@admin.register(ScholarshipResult)
class ScholarshipResultAdmin(admin.ModelAdmin):
    list_display = ('country', 'total_count', 'fetched_at')
    list_filter = ('country', 'fetched_at')
    readonly_fields = ('scholarships_data', 'fetched_at', 'total_count', 'formatted_scholarships')
    fields = ('country', 'formatted_scholarships', 'total_count', 'fetched_at')
    
    def formatted_scholarships(self, obj):
        if not obj.scholarships_data:
            return "No scholarships"
        
        html = "<div style='max-height: 400px; overflow-y: auto;'>"
        for i, scholarship in enumerate(obj.scholarships_data[:10], 1):
            html += f"<div style='border: 1px solid #ddd; margin: 5px; padding: 10px;'>"
            html += f"<strong>{i}. {scholarship.get('name', 'N/A')}</strong><br>"
            html += f"Coverage: {scholarship.get('coverage', 'N/A')}<br>"
            html += f"Eligibility: {scholarship.get('eligibility', 'N/A')}<br>"
            if scholarship.get('link'):
                html += f"<a href='{scholarship['link']}' target='_blank'>View Details</a>"
            html += "</div>"
        if len(obj.scholarships_data) > 10:
            html += f"<p><em>... and {len(obj.scholarships_data) - 10} more scholarships</em></p>"
        html += "</div>"
        return format_html(html)
    
    formatted_scholarships.short_description = "Scholarships Preview"
    
    def save_model(self, request, obj, form, change):
        if not change:
            service = ScholarshipOwlService()
            scholarships = service.get_scholarships(country=obj.country, limit=50)
            obj.scholarships_data = scholarships
            obj.total_count = len(scholarships)
        super().save_model(request, obj, form, change)

class UniversityDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'program_count', 'scholarship_count')
    list_filter = ('country',)
    readonly_fields = ('formatted_programs', 'formatted_scholarships_detail')
    fields = ('name', 'country', 'formatted_scholarships_detail', 'formatted_programs')
    
    def program_count(self, obj):
        return f"{len(obj.bachelor_programs)} bachelor, {len(obj.masters_programs)} masters"
    
    def scholarship_count(self, obj):
        return len(obj.scholarships)
    
    def formatted_scholarships_detail(self, obj):
        if not obj.scholarships:
            return "No scholarships"
        
        html = "<div style='max-height: 300px; overflow-y: auto;'>"
        for i, scholarship in enumerate(obj.scholarships, 1):
            html += f"<div style='border: 1px solid #ddd; margin: 5px; padding: 10px;'>"
            html += f"<strong>{i}. {scholarship.get('name', 'N/A')}</strong><br>"
            html += f"Coverage: {scholarship.get('coverage', 'N/A')}<br>"
            html += f"Eligibility: {scholarship.get('eligibility', 'N/A')}<br>"
            if scholarship.get('link'):
                html += f"<a href='{scholarship['link']}' target='_blank'>View Details</a>"
            html += "</div>"
        html += "</div>"
        return format_html(html)
    
    def formatted_programs(self, obj):
        html = "<div style='max-height: 400px; overflow-y: auto;'>"
        
        if obj.bachelor_programs:
            html += "<h3>Bachelor Programs</h3>"
            for i, program in enumerate(obj.bachelor_programs, 1):
                html += f"<div style='border: 1px solid #e0e0e0; margin: 3px; padding: 8px;'>"
                html += f"<strong>{i}. {program.get('program_name', 'N/A')}</strong><br>"
                html += f"Duration: {program.get('duration_years', 'N/A')} years<br>"
                html += f"Language: {program.get('language', 'N/A')}<br>"
                if program.get('notes'):
                    html += f"Notes: {program.get('notes')}<br>"
                html += "</div>"
        
        if obj.masters_programs:
            html += "<h3>Masters Programs</h3>"
            for i, program in enumerate(obj.masters_programs, 1):
                html += f"<div style='border: 1px solid #e0e0e0; margin: 3px; padding: 8px;'>"
                html += f"<strong>{i}. {program.get('program_name', 'N/A')}</strong><br>"
                html += f"Duration: {program.get('duration_years', 'N/A')} years<br>"
                html += f"Language: {program.get('language', 'N/A')}<br>"
                if program.get('thesis_required'):
                    html += f"Thesis Required: Yes<br>"
                if program.get('notes'):
                    html += f"Notes: {program.get('notes')}<br>"
                html += "</div>"
        
        html += "</div>"
        return format_html(html)
    
    formatted_scholarships_detail.short_description = "Scholarships"
    formatted_programs.short_description = "Programs"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(University, UniversityDataAdmin)