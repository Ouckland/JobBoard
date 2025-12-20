from django.contrib import admin
from .models import JobApplication, JobPosting, Notification, SavedJob


class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'deadline', 'job_status_column')

    def job_status_column(self, obj):
        return obj.verify_job_status()
    
    job_status_column.short_description = 'Job Status'
    job_status_column.admin_order_field = 'deadline'


# Register your models here.

admin.site.register(JobApplication)
admin.site.register(SavedJob)
admin.site.register(Notification)
admin.site.register(JobPosting, JobPostingAdmin)

