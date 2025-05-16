from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


app_name = 'users'
urlpatterns = [
    path('email-sign-up/', views.email_signup_view, name='email_sign_up'),
    path('validate-otp/<str:user_email>/', views.validate_otp, name='validate_otp'),
    path('resend-otp/<str:user_email>/', views.resend_otp, name='resend_otp'),
    path('choose-account-type/', views.choose_account_type_view, name='choose_account_type'),
    path('basic-info/', views.basic_info_view, name='basic_info'),
    path('account-info/', views.account_info_view, name='account_info'),
    path('login/', views.login_view, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('validate-reset-otp/<str:user_email>/', views.validate_reset_otp, name='validate_reset_otp'),
    path('resend-reset-otp/<str:user_email>/', views.resend_reset_otp, name='resend_reset_otp'),
    path('reset-password/<str:user_email>', views.reset_password, name='reset_password')


]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )