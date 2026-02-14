import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.contrib.auth.models import User
from network.models import Profile, MentorRequest

def seed_admin_data():
    # 1. Create Admin User
    admin_user, created = User.objects.get_or_create(username='admin_boss', email='admin@example.com', first_name='Chief', last_name='Admin')
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        profile, _ = Profile.objects.get_or_create(user=admin_user)
        profile.user_type = 'admin'
        profile.save()

    # 2. Create some varied users
    user_data = [
        ('student_raj', 'student', 35),
        ('student_priya', 'student', 42),
        ('alumni_karan', 'alumni', 0),
        ('mentor_neha', 'mentor', 0),
    ]

    for username, role, marks in user_data:
        u, c = User.objects.get_or_create(username=username, email=f'{username}@example.com')
        if c:
            u.set_password('pass123')
            u.save()
            p, _ = Profile.objects.get_or_create(user=u)
            p.user_type = role
            p.assessment_marks = marks
            p.save()

    # 3. Create a Mentor Request
    student = User.objects.get(username='student_raj')
    mentor = User.objects.get(username='mentor_neha')
    MentorRequest.objects.get_or_create(
        student=student,
        mentor=mentor,
        message="I need guidance on Python projects.",
        status='pending'
    )

    print("Admin portal test data seeded successfully!")

if __name__ == '__main__':
    seed_admin_data()
