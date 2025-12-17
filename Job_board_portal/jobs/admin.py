from django.contrib import admin
from django.utils.html import format_html
from .models import JobApplication, JobPosting, Notification, SavedJob, ApplicationReview


class ApplicationReviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'reviewer', 'reviewed_at')
    search_fields = ('application__applicant__full_name', 'reviewer__company_name')


    list_display = ('application', 'reviewer', 'reviewed_at')

class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'application_date')

    def colored_status(self, obj):  
        color_map = {
            'accepted': 'green',
            'rejected': 'red',
            'pending': 'orange',
        }
        color = color_map.get(obj.status.lower(), 'black')
        return format_html('<span style="color: {color}; font-weight: bold;">{status}</span>', color=color, status=obj.status.capitalize())

    colored_status.allow_tags = True
    colored_status.short_description = 'Status'


class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'deadline', 'job_status_column')

    def job_status_column(self, obj):
        return obj.verify_job_status()
    
    job_status_column.short_description = 'Job Status'
    job_status_column.admin_order_field = 'deadline'


# Register your models here.

admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(SavedJob)
admin.site.register(Notification)
admin.site.register(ApplicationReview, ApplicationReviewAdmin)
admin.site.register(JobPosting, JobPostingAdmin)

