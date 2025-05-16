from django.contrib import admin
from .models import Profile, SeekerProfile, EmployerProfile
# Register your models here.
admin.site.register(SeekerProfile)
admin.site.register(EmployerProfile)