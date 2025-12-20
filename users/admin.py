from django.contrib import admin
from .models import Profile, SeekerProfile, EmployerProfile, KnownDevice, SecurityLog
# Register your models here.
# class SeekerprofileField(admin.ModelAdmin):

admin.site.register(SeekerProfile)
admin.site.register(EmployerProfile)
admin.site.register(KnownDevice)
admin.site.register(SecurityLog)