
# Jobsphere Profile & Authentication Roadmap

**Date:** June 24, 2025

## ✅ Features You’ve Already Completed

### 🔐 Authentication System
- Signup with email & password
- OTP verification (including expiry check)
- Account type selection (seeker or employer)
- Profile completion before login
- Session handling and flushing
- Welcome notification after setup

### 👤 Profile Management
- Abstract base `Profile` model with shared fields
- SeekerProfile & EmployerProfile models
- Full CRUD (Create, Read, Update) for profile data
- Split forms for basic and account info
- Update via POST forms with file upload support
- Dynamic forms depending on account type

### 📸 Profile Image Update
- Profile picture and company logo uploads
- Image preview with clickable upload on profile page

### 📊 Profile Completion Tracker
- Real-time profile completeness bar
- Auto-calculate based on filled fields

### 🔓 Password Reset Flow
- Forgot password with OTP to email
- OTP validation with expiry handling
- Password reset and success notification

### 🔐 Login System Enhancements
- Session-based welcome messages
- Known device detection using user-agent
- Unfamiliar device notifications
- Regular login success notification

### 🌍 Public Profile
- Accessible via `/profile/<username>/`
- Read-only display of public data
- Separated template with styling

---

## 🧠 Ideas You Can Add Next

### 📩 Notifications
- Convert notifications to async (Celery)
- Allow users to mark as read/delete notifications

### 📬 Email Enhancements
- Send HTML formatted emails
- Add email verification links

### 👀 Activity Logs
- Login history
- Password reset logs

### 🗂️ Account Deletion
- Safe user deletion with optional export
- “Delete my account” request page

### 📥 Resume Download (for seekers)
- Public download link for resumes

### 📅 Application Tracker
- For seekers: view applied jobs
- For employers: manage posted jobs

---

## 🧵 Celery: Do You Need It Now?

You **don’t absolutely need** Celery now, but it’s worth considering if:
- Email sending or notifications delay page load
- You want to run scheduled background tasks (e.g. cleanup expired OTPs)
- You plan to scale up or move to production

If yes, start with:
- Setting up Redis locally
- Adding Celery to your Django project
- Offloading email + notification tasks to Celery

