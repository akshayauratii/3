import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.contrib.auth.models import User
from network.models import Opportunity, Application, Connection, Notification, Profile, SuccessStory

# Create a dummy user for posting if not exists
admin_user, _ = User.objects.get_or_create(username='admin_poster')
if admin_user.pk is None:
    admin_user.set_password('admin123')
    admin_user.save()

# Ensure we have a student user to apply
student_user, _ = User.objects.get_or_create(username='student_demo')
if student_user.pk is None:
    student_user.set_password('student123')
    student_user.save()

student_profile, _ = Profile.objects.get_or_create(user=student_user)
student_profile.user_type = 'student'
student_profile.assessment_marks = 28
student_profile.skills = "Python, Django, HTML, CSS, JavaScript"
student_profile.save()

# Create some dummy connections
c1_user, _ = User.objects.get_or_create(username='alumni_jane')
c2_user, _ = User.objects.get_or_create(username='student_bob')
Connection.objects.get_or_create(user=student_user, connected_user=c1_user)
Connection.objects.get_or_create(user=student_user, connected_user=c2_user)

# Create some dummy notifications
Notification.objects.get_or_create(user=student_user, message="Your application to TechCorp was viewed.")
Notification.objects.get_or_create(user=student_user, message="New mentor match available: John Doe.")
Notification.objects.get_or_create(user=student_user, message="Reminder: 'Chai Time' session starts in 1 hour.")

opportunities = [
    # Govt Jobs
    {
        'title': 'Junior Engineer',
        'description': 'Public Works Department recruitment for civil engineers. Requires B.Tech in Civil Engineering.',
        'type': 'job',
        'category': 'govt',
        'company': 'PWD',
        'location': 'New Delhi',
        'min_assessment_score': 25
    },
    {
        'title': 'Research Scientist B',
        'description': 'ISRO recruitment for scientists. Candidates must have M.Tech/Ph.D in related field.',
        'type': 'job',
        'category': 'govt',
        'company': 'ISRO',
        'location': 'Bangalore',
        'min_assessment_score': 28
    },
    {
        'title': 'Bank PO',
        'description': 'Probationary Officer recruitment by SBI. Any graduate can apply. Written exam required.',
        'type': 'job',
        'category': 'govt',
        'company': 'SBI',
        'location': 'Mumbai',
        'min_assessment_score': 22
    },
    {
        'title': 'Assistant Section Officer',
        'description': 'Recruitment for Ministry of External Affairs via SSC CGL.',
        'type': 'job',
        'category': 'govt',
        'company': 'MEA',
        'location': 'New Delhi',
        'min_assessment_score': 26
    },
    
    # Private Jobs - Tech
    {
        'title': 'Software Developer',
        'description': 'Full stack developer role. MERN stack expertise required. 0-2 years experience.',
        'type': 'job',
        'category': 'private',
        'company': 'TechCorp',
        'location': 'Pune',
        'min_assessment_score': 20
    },
    {
        'title': 'Frontend Engineer',
        'description': 'React.js and Tailwind CSS specialist needed for a fast-growing fintech startup.',
        'type': 'job',
        'category': 'private',
        'company': 'FinGrow',
        'location': 'Bangalore',
        'min_assessment_score': 22
    },
    {
        'title': 'Data Analyst',
        'description': 'Analyze large datasets using Python and SQL. Create dashboards in Tableau.',
        'type': 'job',
        'category': 'private',
        'company': 'DataWise',
        'location': 'Hyderabad',
        'min_assessment_score': 24
    },
    {
        'title': 'DevOps Engineer',
        'description': 'Manage AWS infrastructure and CI/CD pipelines. Knowledge of Docker and Kubernetes essential.',
        'type': 'job',
        'category': 'private',
        'company': 'CloudNine',
        'location': 'Remote',
        'min_assessment_score': 25
    },

    # Private Jobs - Marketing & Creative
    {
        'title': 'Digital Marketing Specialist',
        'description': 'Manage SEO, SEM, and social media campaigns. Google Analytics certification preferred.',
        'type': 'job',
        'category': 'private',
        'company': 'GrowthHackers',
        'location': 'Mumbai',
        'min_assessment_score': 18
    },
    {
        'title': 'Content Writer',
        'description': 'Write engaging blog posts and website copy for tech clients. Excellent English skills required.',
        'type': 'job',
        'category': 'private',
        'company': 'CopyPro',
        'location': 'Remote',
        'min_assessment_score': 18
    },
    {
        'title': 'Graphic Designer',
        'description': 'Create visual assets for social media and marketing. Proficiency in Adobe Creative Suite required.',
        'type': 'job',
        'category': 'private',
        'company': 'CreativeStudio',
        'location': 'Delhi',
        'min_assessment_score': 19
    },

    # Govt Internships
    {
        'title': 'Summer Intern',
        'description': 'NITI Aayog Internship Scheme. Research and policy analysis role.',
        'type': 'internship',
        'category': 'govt',
        'company': 'NITI Aayog',
        'location': 'New Delhi',
        'min_assessment_score': 25
    },
    {
        'title': 'Research Intern',
        'description': 'Internship at DRDO labs for engineering students.',
        'type': 'internship',
        'category': 'govt',
        'company': 'DRDO',
        'location': 'Hyderabad',
        'min_assessment_score': 27
    },

    # Private Internships
    {
        'title': 'Marketing Intern',
        'description': 'Social media marketing internship. Assist in campaign planning and execution.',
        'type': 'internship',
        'category': 'private',
        'company': 'BrandNice',
        'location': 'Mumbai',
        'min_assessment_score': 15
    },
    {
        'title': 'SDE Intern',
        'description': 'Software Development Engineer Intern. Work on live projects with senior developers.',
        'type': 'internship',
        'category': 'private',
        'company': 'InnovateTech',
        'location': 'Bangalore',
        'min_assessment_score': 23
    },
    {
        'title': 'HR Intern',
        'description': 'Assist in recruitment processes and employee engagement activities.',
        'type': 'internship',
        'category': 'private',
        'company': 'PeopleFirst',
        'location': 'Pune',
        'min_assessment_score': 16
    }
]

created_opps = []
for app_data in opportunities:
    opp, created = Opportunity.objects.get_or_create(title=app_data['title'], defaults={'posted_by': admin_user, **app_data})
    created_opps.append(opp)

# Create Dummy Applications for student_demo
# 1. Applied to TechCorp (Private Job)
Application.objects.get_or_create(
    user=student_user,
    opportunity=created_opps[2], # Software Developer
    defaults={'status': 'applied'}
)

# 2. Applied to NITI Aayog (Govt Internship)
Application.objects.get_or_create(
    user=student_user,
    opportunity=created_opps[3], # Summer Intern
    defaults={'status': 'applied'}
)

# 3. Interview for ISRO (Govt Job)
Application.objects.get_or_create(
    user=student_user,
    opportunity=created_opps[1], # ISRO
    defaults={
        'status': 'interview',
        'interview_date': timezone.now() + timedelta(days=5)
    }
)

# Create Success Stories
# We need alumni type profiles first
alumni_data = [
    {
        'username': 'alumni_sarah', 'name': 'Sarah Jenkins', 'grad_year': 2018,
        'title': 'From Campus to CEO',
        'story': "I started my journey with a small idea in my dorm room. The alumni network connected me with my first investor. Today, my tech startup employs over 50 people and we're just getting started. Never underestimate the power of networking!"
    },
    {
        'username': 'alumni_david', 'name': 'David Chen', 'grad_year': 2020,
        'title': 'Global Impact Award Winner',
        'story': "Working on sustainable engineering solutions for developing nations has been my dream. The mentorship I received during my final year guided me to the right fellowship. Now I'm leading a project that brings clean water to thousands."
    },
    {
        'username': 'alumni_emily', 'name': 'Emily Rodriguez', 'grad_year': 2019,
        'title': 'Research Breakthrough in Biotech',
        'story': "Research was always my passion. Thanks to the portal, I found a research assistant position at a top institute. Three years later, our team has made a significant breakthrough in cancer research. Grateful for the guidance."
    },
    {
        'username': 'alumni_raj', 'name': 'Raj Patel', 'grad_year': 2021,
        'title': 'Innovating in EdTech',
        'story': "I wanted to make education accessible to everyone. The feedback from alumni mentors helped me refine my platform. We simply launched 'LearnEasy' and it's already helping 10,000+ students across the state."
    }
]

for item in alumni_data:
    u, _ = User.objects.get_or_create(username=item['username'])
    if u.pk is None:
        u.set_password('alumni123')
        u.first_name = item['name'].split()[0]
        u.last_name = item['name'].split()[1]
        u.save()
    
    p, _ = Profile.objects.get_or_create(user=u)
    p.user_type = 'alumni'
    p.save()

    SuccessStory.objects.get_or_create(
        alumni=p,
        title=item['title'],
        defaults={
            'story': item['story'],
            'graduation_year': item['grad_year']
        }
    )

print("Dummy data including skills, connections, notifications, and success stories created.")

print("Dummy data including skills, connections, and notifications created.")
