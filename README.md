# 💼 Jobsphere — Smart Job Board Platform

🔗 **Live Demo:** TBA  
👨‍💻 **Author:** [@Ouckland](https://github.com/Ouckland)  
📧 **Email:** iselekorede5@gmail.com  
🔗 **LinkedIn:** [Korede Isele](https://www.linkedin.com/in/korede-isele-944016297/)

---

**Jobsphere** is a modern job board web application built with **Django**, designed to connect job seekers and employers seamlessly.  
It features secure authentication, profile completion tracking, public profiles, job postings, and responsive dashboards for both user types.

---

## 🚀 Core Features

### 🔐 Authentication System
- Email + Password signup  
- OTP verification with expiry  
- Account type selection (Seeker / Employer)  
- Profile completion before login  
- Session handling and welcome notifications  
- Password reset via OTP  

### 👤 Profile Management
- Abstract base `Profile` model with shared fields  
- Separate **SeekerProfile** and **EmployerProfile** models  
- Full Create, Read, Update (no delete)  
- Profile image and company logo upload  
- Dynamic forms depending on account type  
- Real-time profile completion progress bar  

### 🌍 Public Profiles
- Each user has a public URL → `/profile/<username>/`  
- Read-only profile display for visitors  
- Public directory:
  - **Browse Candidates**
  - **Browse Employers**

### 🧭 Dashboards
- **Job Seekers:**  
  - Search and filter available jobs  
  - See recommended jobs  
  - Track job applications and their statuses  
- **Employers:**  
  - Post and manage jobs  
  - View applicants per job  
  - Monitor application stats and status updates  

### 💬 Notifications
- AJAX-powered notifications (mark as read without page reload)  
- Delivered for key actions (applications, profile updates, etc.)

### 🎨 UI / UX
- Ocean-inspired dark theme 🌊  
- Responsive design for mobile and desktop  
- Reusable header with hamburger menu  
- Glassmorphism elements for modern aesthetics  

---

## 🔨 Current Focus

### 🧾 Application Review System *(In Progress)*
**For Employers:**
- View all applicants per job  
- See applicant details & CV  
- Update application status:
  - Pending → Shortlisted → Interviewed → Hired / Rejected  

**For Seekers:**
- View all jobs applied to  
- Track progress through clear status updates  

---

## 📈 Future Enhancements (Phase 2)
- In-app messaging system 💬  
- Saved jobs & saved candidates  
- Advanced job recommendations  
- Employer analytics (views, reach)  
- Subscription / payment system  
- Async notifications with Celery + Redis  

---

## 🛠️ Tech Stack

| Layer | Technology |
|--------|-------------|
| **Backend** | Django (Python) |
| **Frontend** | HTML5, CSS3, JS |
| **Database** | SQLite (default) / PostgreSQL (production-ready) |
| **Authentication** | Django’s built-in auth + OTP system |
| **Hosting** | Render (Free Tier) |

---

## ⚙️ Setup Instructions

```bash
# 1️⃣ Clone the repository
git clone https://github.com/Ouckland/JobSphere.git
cd JobSphere

# 2️⃣ Create a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Apply migrations
python manage.py migrate

# 5️⃣ Run the development server
python manage.py runserver
