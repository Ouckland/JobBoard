import random
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import OTP, Profile, EmployerProfile, SeekerProfile

from .forms import EmailSignupForm, User, OTPform, ChooseAccountTypeForm, EmployerBasicInfoForm, SeekerBasicInfoForm
from .forms import EmployerAccountForm, SeekerAccountForm, LoginForm , PassewordResetRequestForm, PasswordResetForm

from django.utils import timezone

def email_signup_view(request):
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email in use already!Try another one or login')
            
            # Prevent duplicate OTP entries for same email
            existing_otp = OTP.objects.filter(user_email=email)
            if existing_otp.exists():
                messages.error(request, 'A user with this email already exists. Please log in or use a different email.')
                return redirect('users:email_sign_up')

            # Generate OTP
            otp = str(random.randint(100000, 999999))

            # Store OTP in the database or update if it already exists
            OTP.objects.update_or_create(
                user_email=email,
                defaults={'otp': otp, 'created_at': timezone.now()}
            )

            # Store signup data in session temporarily
            request.session['signup_email'] = email
            request.session['signup_form_data'] = form.cleaned_data

            # Send OTP to email
            send_mail(
                subject='Email OTP Verification',
                message=f"Hello,\n\nYour OTP for account creation is: {otp}\n\n- Jobsphere",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )

            messages.info(request, f'OTP sent to {email}')
            return redirect('users:validate_otp', user_email=email)
    else:
        form = EmailSignupForm()

    return render(request, 'user/signup.html', {'form': form})



def validate_otp(request, user_email):
    signup_data = request.session.get('signup_form_data')
    if not signup_data:
        messages.error(request, 'Session expired. Please try signing up again.')
        return redirect('users:email_signup')

    otp_form = OTPform(user_email=user_email)

    if request.method == 'POST':
        otp_form = OTPform(request.POST, user_email=user_email)
        if otp_form.is_valid():
            entered_otp = otp_form.cleaned_data.get('otp')

            try:
                otp_object = OTP.objects.get(user_email=user_email)

                if entered_otp == otp_object.otp:
                    otp_object.delete()

                    messages.success(request, 'OTP verified successfully. Please complete your profile to proceed.')
                    return redirect('users:choose_account_type')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')

            except OTP.DoesNotExist:
                messages.error(request, 'OTP has expired or does not exist.')

        else:
            messages.error(request, 'Invalid form submission. Please enter a valid OTP.')

    return render(request, 'user/validate-otp.html', {'form': otp_form, 'user_email': user_email})

def resend_otp(request, user_email):
    user_email = request.session.get('signup_email')
    if not user_email:
        messages.error(request, 'Session expired. Please try signing up again.')
        return redirect('users:email_sign_up')

    if request.method == 'GET':
        otp = OTP.objects.get(user_email=user_email)
        if not otp.is_expired:
            messages.error(request, 'OTP code is still valid. Wait for a while and try again!')
            return redirect('users:validate_otp', user_email=user_email)    
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in the database or update if it already exists
        OTP.objects.update_or_create(
            user_email=user_email,
            defaults={'otp': otp, 'created_at': timezone.now()}
        )

        send_mail(
                subject='Email OTP Verification',
                message=f"Hello,\n\nYour OTP for account creation is: {otp}\n\n- Jobsphere",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )

        messages.info(request, f'OTP sent to {user_email}')
        return redirect('users:validate_otp', user_email=user_email)
    return render(request, 'user/validate-otp.html', {'user_email': user_email})

def choose_account_type_view(request):
    user_email = request.session.get('signup_email')
    sign_up_data = request.session.get('signup_form_data')
    password = sign_up_data.get('password')
    
    if not user_email and password:
        return redirect('users:email_signup')

    form = ChooseAccountTypeForm(user_email=user_email)

    if request.method == 'POST':
        form = ChooseAccountTypeForm(user_email=user_email, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            account_type = form.cleaned_data.get('account_type')

            # Create the user
            user = User
            
            # Check if username is already in use
            if user.objects.filter(username=username).exists():
                messages.error(request, "Username already exists! Please try another one")
                return redirect('users:choose_account_type')

            user = User.objects.create_user(
                username=username,
                email=user_email,
                password=password
            )
            user.is_active = False  # Inactive until profile is completed
            user.save()

            # Create related profile (SeekerProfile or EmployerProfile) based on account type
            if account_type == 'seeker':
                SeekerProfile.objects.create(user=user)
            elif account_type == 'employer':
                EmployerProfile.objects.create(user=user)

            # Store user id and account type in session
            request.session['pending_user_id'] = user.id
            request.session['account_type'] = account_type

            return redirect('users:basic_info')  # Redirect to basic info page

    return render(request, 'user/account-type.html', {'form': form})


def basic_info_view(request):
    user_id = request.session.get('pending_user_id')

    if not user_id:
        return redirect('users:choose_account_type')  # Redirect if user hasn't been created

    user = User.objects.get(id=user_id)  # Get the user from the session data
    account_type = request.session.get('account_type')

    # Define forms based on account type
    if account_type == 'employer':
        form = EmployerBasicInfoForm()
    else:
        form = SeekerBasicInfoForm()

    if request.method == 'POST':
        form = form.__class__(request.POST, request.FILES)  # Handle form submission
        if form.is_valid():
            request.session['basic_form_data'] = form.cleaned_data
            return redirect('users:account_info')  # Go to the account info page to fill out more data

    return render(request, 'user/basic-info.html', {'form': form})


def account_info_view(request):
    user_id = request.session.get('pending_user_id')
    account_type = request.session.get('account_type')
    user = get_object_or_404(User, id=user_id)

    FormClass = SeekerAccountForm if account_type == 'seeker' else EmployerAccountForm
    form = FormClass()
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            basic_info_data = request.session.get('basic_info', {})

            if account_type == 'seeker':
                profile = SeekerProfile(user=user, **basic_info_data)
                form = SeekerAccountForm(request.POST, request.FILES, instance=profile)
            
            else:
                profile = EmployerProfile(user=user, **basic_info_data)
                form = EmployerAccountForm(request.POST, request.FILES, instance=profile)
            
        
            # form.save()
            user.is_active = True
            user.save()
            request.session.flush()
            messages.success(request, 'Account setup succesful. Please log in.')
            return redirect('users:login')

            
    return render(request, 'user/account-info.html', context={'form': form, 'account_type': account_type})



def login_view(request):
    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate user with username and password
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful.')
                return redirect('jobs:dashboard')  # Redirect to dashboard or home page
            else:
                messages.error(request, 'Invalid credentials. Please check your username and password.')

    return render(request, 'user/login.html', {'form': form})

def forgot_password(request):


    form = PassewordResetRequestForm()
    if request.method == 'POST':
        form = PassewordResetRequestForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email')
                return redirect('users:forgot_password')
            otp = str(random.randint(100000, 999999))
            OTP.objects.update_or_create(
            user_email=user_email,
            defaults={'otp': otp, 'created_at': timezone.now()}
        )

        send_mail(
                subject='Password Reset OTP',
                message=f"Hello,\n\nYour OTP for resetting your password is: {otp}\n\n- Jobsphere",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )
        request.session['user_email'] = user_email

        messages.info(request, f'OTP sent to {user_email}')
        return redirect('users:validate_reset_otp', user_email=user_email)
    return render(request, 'user/forgot-password.html', {'form': form})

def validate_reset_otp(request, user_email):
    user_email = request.session.get('user_email')
    if not user_email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('users:forgot_password')
    form = OTPform(user_email=user_email)
    if request.method == 'POST':
        form = OTPform(request.POST, user_email=user_email)
        if form.is_valid():
            entered_otp = form.cleaned_data.get('otp')
            try:
                otp_object = OTP.objects.get(user_email=user_email)

                if entered_otp == otp_object.otp:
                    otp_object.delete()

                    messages.success(request, 'OTP verified successfully. Please reset your password to proceed.')
                    return redirect('users:reset_password', user_email=user_email)
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')

            except OTP.DoesNotExist:
                messages.error(request, 'OTP has expired or does not exist.')

        else:
            messages.error(request, 'Invalid form submission. Please enter a valid OTP.')

    return render(request, 'user/validate-reset-otp.html', {'form': form, 'user_email': user_email})    

def resend_reset_otp(request, user_email):

    user_email = request.session.get('user_email')
    if not user_email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('users:forgot_password')

    if request.method == 'GET':
        otp = OTP.objects.get(user_email=user_email)
        if not otp.is_expired:
            messages.error(request, 'OTP code is still valid. Wait for a while and try again!')
            return redirect('users:validate_reset_otp', user_email=user_email)    
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in the database or update if it already exists
        OTP.objects.update_or_create(
            user_email=user_email,
            defaults={'otp': otp, 'created_at': timezone.now()}
        )

        send_mail(
                subject='Password Reset Verification',
                message=f"Hello,\n\nYour OTP for password reset is: {otp}\n\n- Jobsphere",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )

        messages.info(request, f'OTP sent to {user_email}')
        return redirect('users:validate_reset_otp', user_email=user_email)
    return render(request, 'user/resend-reset-otp.html', {'user_email': user_email})

def reset_password(request, user_email):
    user_email = request.session.get('user_email')
    if not user_email:
        messages.error(request, 'Session has expired, please try again')
        return redirect('users:forgot_password')
    
    form = PasswordResetForm()
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            user = User.objects.get(email=user_email)
            user.set_password(password)
            user.save()
            request.session.clear()
            messages.success(request, 'Password reset succesful. Login to continue')
            return redirect('users:login')
    return render(request, 'user/reset-password.html', {'form': form, 'user_email': user_email})