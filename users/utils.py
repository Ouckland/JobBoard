# utils.py
from django.shortcuts import get_object_or_404
from .models import SeekerProfile, EmployerProfile

def get_available_providers(profile):
    """Return different providers based on profile type"""
    if profile.account_type == 'seeker':
        return ['google', 'github', 'linkedin']
    elif profile.account_type == 'employer':
        return ['google', 'linkedin', 'xing']
    return []