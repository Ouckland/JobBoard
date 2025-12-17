from django.urls import path
from . import views


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
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),

    path('view-profile', views.profile, name='view_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),   
    path('profile/update/basic-info/', views.update_basic_info, name='update_basic_info'),   
    path('profile/update/account-info/', views.update_account_info, name='update_account_info'),
    path('profile/update/picture/', views.update_profile_picture, name='update_profile_picture'),   
    
    path('profile/account/view/', views.account_settings, name='account_settings'),
    path('profile/account/password/change/', views.change_password, name='change_password'),
    path('profile/account/delete/confirm/', views.delete_account, name='delete_account'),


    path('profile/<str:username>/', views.public_profile, name='public_profile'),

    path('ajax/load-states/', views.load_states, name='ajax_load_states'),

]
