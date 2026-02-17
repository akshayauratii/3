import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.contrib.auth.models import User
from network.models import Profile

def seed_mentors():
    # Ensure some alumni users exist as mentors
    mentor_data = [
        {'username': 'Akshaya', 'email': 'akshaya@example.com', 'bio': 'Passionate about helping students navigate their career paths.', 'skills': 'Python, Django, AWS'},
        {'username': 'Akkie', 'email': 'akkie@example.com', 'bio': 'Experienced professional with a love for teaching and mentoring.', 'skills': 'React, Node.js, MongoDB'},
        {'username': 'Ramya', 'email': 'ramya@example.com', 'bio': 'Tech enthusiast and open source contributor.', 'skills': 'Data Science, ML, AI'},
        {'username': 'Pulli', 'email': 'pulli@example.com', 'bio': 'Building scalable systems and leading engineering teams.', 'skills': 'Java, Spring Boot, Microservices'},
        {'username': 'Divya', 'email': 'divya@example.com', 'bio': 'believe in the power of community and continuous learning.', 'skills': 'UI/UX, Figma, Adobe XD'},
        {'username': 'Divvu', 'email': 'divvu@example.com', 'bio': 'Always happy to connect and share my journey.', 'skills': 'Cybersecurity, Network Security'},
        {'username': 'Harri', 'email': 'harri@example.com', 'bio': 'Expert in the field with 5+ years of industry experience.', 'skills': 'Cloud Computing, Azure, DevOps'},
        {'username': 'Akanksha', 'email': 'akanksha@example.com', 'bio': 'Dedicated to empowering women in tech.', 'skills': 'Flutter, Dart, Firebase'}
    ]

    for data in mentor_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            email=data['email']
        )
        if created:
            user.set_password('mentor123')
            user.save()
            
        profile, p_created = Profile.objects.get_or_create(user=user)
        profile.user_type = 'alumni'
        profile.bio = data['bio']
        profile.skills = data['skills']
        profile.save()

    print("Mentor data seeded successfully!")

if __name__ == '__main__':
    seed_mentors()
